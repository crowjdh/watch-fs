# Dev
- Run
  ```bash
  python watch.py $TARGET $LIMIT [test]
  ```
- Run in background
  ```bash
  nohup ./watch $TARGET $LIMIT [test] > /dev/null 2>&1 &
  ```

# Build
```bash
pip3 install pyinstaller
pip3 install -r requirements.pip
python3 -m PyInstaller -y watch.py
```
