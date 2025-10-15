# How to Access Using dts.com:8000

## On Your Server Machine (This Computer)
Run the setup script:
```bash
cd /home/gss/Desktop/dts/test_platform
./setup_dts_hostname.sh
```

You'll need to enter your sudo password to modify /etc/hosts.

## On Other Devices in Your Network

### Windows:
1. Open Notepad as Administrator
2. Open file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line at the end:
   ```
   192.168.29.81    dts.com
   ```
4. Save the file

### macOS:
1. Open Terminal
2. Run: `sudo nano /etc/hosts`
3. Add this line:
   ```
   192.168.29.81    dts.com
   ```
4. Save with Ctrl+O, exit with Ctrl+X

### Linux:
1. Open Terminal
2. Run: `sudo nano /etc/hosts`
3. Add this line:
   ```
   192.168.29.81    dts.com
   ```
4. Save with Ctrl+O, exit with Ctrl+X

### Android:
- Requires root access OR
- Use a local VPN app like "Virtual Hosts" or "Hosts Go"

### iOS:
- Use an app like "Hosts.dnsforge" (no jailbreak required)
- Or configure a custom DNS profile

## Testing
After setup, you can access your Django app from any device using:
`http://dts.com:8000`

## Important Notes:
- This is for local network only - dts.com won't work outside your network
- Each device needs the hosts file entry
- If your server IP changes, update all hosts files