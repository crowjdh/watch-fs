# Dev
- Run
  ```bash
  python watch.py $TARGET $LIMIT [test]
  ```
- Run in background
  ```bash
  nohup ./watch $TARGET $LIMIT [test] > /dev/null 2>&1 &
  ```

# Tips
- gate road
  ```bash
  /var/lib/motioneye/Camera1
  sudo systemctl status watch-motion.service
  ```
- Others
  ```
  cd /data/workspace/watch-armhf
  ./watch /data/output/Camera1 5
  ```

# Build
```bash
pip3 install pyinstaller
pip3 install -r requirements.pip
python3 -m PyInstaller -y watch.py
```
