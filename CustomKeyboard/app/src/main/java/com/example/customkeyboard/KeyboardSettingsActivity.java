package com.example.customkeyboard;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

public class KeyboardSettingsActivity extends AppCompatActivity {
    TextView statusText;

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           String permissions[], int[] grantResults) {
        updateStatus();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.keyboard_settings_view);
        statusText = findViewById(R.id.status_text);
        if (ActivityCompat.checkSelfPermission(KeyboardSettingsActivity.this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(KeyboardSettingsActivity.this, new
                    String[]{Manifest.permission.CAMERA}, 201);
        }

        updateStatus();
        setCheckBox();
    }

    private void setCheckBox() {
        SharedPreferences sharedPref = getSharedPref();
        boolean checked = sharedPref.getBoolean("show_data", true);
        CheckBox checkbox = findViewById(R.id.checkbox_show_scanned_data);
        checkbox.setChecked(checked);
    }

    public void updateStatus() {
        if (ActivityCompat.checkSelfPermission(KeyboardSettingsActivity.this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            statusText.setText(R.string.missing_camera_permission);
        } else {
            SharedPreferences sharedPref = getSharedPref();
            if (!sharedPref.contains("key")) {
                statusText.setText(R.string.no_key);
            } else {
                statusText.setText(R.string.setup_correct);
            }
        }
    }

    public void storeKey(View view) {
        EditText editText = findViewById(R.id.key_input);
        String value = editText.getText().toString();
        SharedPreferences sharedPref = getSharedPref();
        SharedPreferences.Editor editor = sharedPref.edit();
        editor.putString("key", value);
        editor.apply();
        editText.setText("");

        updateStatus();
    }

    public void onCheckboxShowDataClicked(View view) {
        boolean checked = ((CheckBox) view).isChecked();
        SharedPreferences sharedPref = getSharedPref();
        SharedPreferences.Editor editor = sharedPref.edit();
        editor.putBoolean("show_data", checked);
        editor.apply();
    }

    public SharedPreferences getSharedPref() {
        return getApplicationContext().getSharedPreferences("data", Context.MODE_PRIVATE);
    }
}