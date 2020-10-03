package com.example.customkeyboard;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.inputmethodservice.InputMethodService;
import android.text.TextUtils;
import android.util.Base64;
import android.util.SparseArray;
import android.view.HapticFeedbackConstants;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.widget.TextView;

import androidx.core.app.ActivityCompat;

import com.google.android.gms.common.util.ArrayUtils;
import com.google.android.gms.vision.CameraSource;
import com.google.android.gms.vision.Detector;
import com.google.android.gms.vision.barcode.Barcode;
import com.google.android.gms.vision.barcode.BarcodeDetector;

import java.io.IOException;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class BarcodeInputMethodService extends InputMethodService {
    private SurfaceView surfaceView;
    private BarcodeDetector barcodeDetector;
    private CameraSource cameraSource;

    private TextView barcodeText;
    private String barcodeData;


    public void clearData() {
        barcodeData = "";
        if (barcodeText != null)
            barcodeText.setText("Waiting for scan");
        if (cameraSource != null)
            cameraSource.stop();
        if (surfaceView != null) {
            // clear the camera
            surfaceView.setVisibility(View.INVISIBLE);
            surfaceView.setVisibility(View.VISIBLE);
        }
    }

    @Override
    public View onCreateInputView() {
        // get the KeyboardView and add our Keyboard layout to it
        View keyboardView = getLayoutInflater().inflate(R.layout.keyboard_view, null);
        surfaceView = keyboardView.findViewById(R.id.surface_view);
        barcodeText = keyboardView.findViewById(R.id.barcode_text);

        initialiseDetectorsAndSources();
        return keyboardView;
    }

    @Override
    public void onStartInputView(EditorInfo info, boolean restarting) {
        super.onStartInputView(info, restarting);
    }

    @Override
    public void onFinishInput() {
        super.onFinishInput();
        clearData();
    }

    public void scanOnClick(View view) {
        clearData();
        try {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                cameraSource.start(surfaceView.getHolder());
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void useOnClick(View view) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;

        ic.commitText(barcodeData, 1);
        clearData();
    }

    public void deleteOnClick(View view) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        CharSequence selectedText = ic.getSelectedText(0);
        if (TextUtils.isEmpty(selectedText))
            ic.deleteSurroundingText(1, 0);
        else
            ic.commitText("", 1);
    }


    public void clearOnClick(View view) {
        clearData();
    }

    private void initialiseDetectorsAndSources() {
        barcodeDetector = new BarcodeDetector.Builder(this)
                .setBarcodeFormats(Barcode.ALL_FORMATS)
                .build();

        cameraSource = new CameraSource.Builder(this, barcodeDetector)
                // .setRequestedPreviewSize(1920, 1080)
                .setAutoFocusEnabled(true) //you should add this feature
                .build();

        surfaceView.getHolder().addCallback(new SurfaceHolder.Callback() {
            @Override
            public void surfaceCreated(SurfaceHolder holder) { }

            @Override
            public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) { }

            @Override
            public void surfaceDestroyed(SurfaceHolder holder) {
                clearData();
            }
        });


        barcodeDetector.setProcessor(new Detector.Processor<Barcode>() {
            @Override
            public void release() { }

            @Override
            public void receiveDetections(Detector.Detections<Barcode> detections) {
                final SparseArray<Barcode> barcodes = detections.getDetectedItems();
                if (barcodes.size() != 0) {
                    barcodeText.post(new Runnable() {
                        @Override
                        public void run() {
                            cameraSource.stop();
                            surfaceView.performHapticFeedback(HapticFeedbackConstants.CONFIRM);

                            barcodeData = barcodes.valueAt(0).displayValue;
                            barcodeData = parseScannedData(barcodeData);

                            SharedPreferences sharedPref = getSharedPref();
                            boolean show_data = sharedPref.getBoolean("show_data", true);
                            if (show_data)
                                barcodeText.setText(barcodeData);
                            else
                                barcodeText.setText("***");
                        }
                    });
                }
            }
        });
    }

    final int TAG_SIZE = 16;

    public SharedPreferences getSharedPref() {
        return getApplicationContext().getSharedPreferences("data", Context.MODE_PRIVATE);
    }

    private String parseScannedData(String scanned_data) {
        SharedPreferences sharedPref = getSharedPref();
        String key = sharedPref.getString("key", "");
        String prefix = "mydata:";
        if (scanned_data.startsWith(prefix)) {
            String data = scanned_data.substring(prefix.length());
            try {
                byte[] data_concat = Base64.decode(data, Base64.DEFAULT);
                byte[] tag = Arrays.copyOfRange(data_concat, 0, TAG_SIZE);
                byte[] nonce = Arrays.copyOfRange(data_concat, TAG_SIZE, 2 * TAG_SIZE);
                byte[] text = Arrays.copyOfRange(data_concat, 2 * TAG_SIZE, data_concat.length);

                byte[] key_bytes = Base64.decode(key, Base64.DEFAULT);

                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                SecretKeySpec keySpec = new SecretKeySpec(key_bytes, "AES");
                GCMParameterSpec spec = new GCMParameterSpec(TAG_SIZE * 8, nonce);
                cipher.init(Cipher.DECRYPT_MODE, keySpec, spec);

                byte[] decrypt_array = ArrayUtils.concatByteArrays(text, tag);
                byte[] decodedData = cipher.doFinal(decrypt_array);
                String decryptedText = new String(decodedData, "UTF-8");
                scanned_data = decryptedText;


            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return scanned_data;
    }


}