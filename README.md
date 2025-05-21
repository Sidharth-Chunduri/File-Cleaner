
# ML-Powered Junk File Cleaner

This is a desktop application that uses a machine learning model to identify and help users delete unnecessary files from their system.

## Features

- Scan any directory
- Uses a trained ML model to classify files as junk
- Interactive table to review file details
- Select individual files to delete or delete all detected junk files

### Requirements

- Python 3.8 or higher

## Running the App

Make sure the following files are present in the root directory:
- `webApp.py` (main application)
- `junk_file_model.pkl` (trained classifier)
- `preprocessor.pkl` (feature preprocessing pipeline)

Then run:

```bash
streamlit run webApp.py
```

This will launch the app in your web browser. From there, you can select a folder, review detected junk files, and delete them as needed.

## Notes

- The deletion process is irreversible. Use with caution.
- You can adapt the ML model by retraining it with a different dataset using `prepareData.py`.

## License

This project is licensed under the MIT License.
