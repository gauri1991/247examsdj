# Hostname Setup for Local Network Access

## Option 1: Use .local domain (mDNS/Avahi) - RECOMMENDED
Your system likely already supports mDNS. You can access your Django app using:
- `http://gss-HP-Pavilion-Notebook-15.local:8000`

This works automatically on most Linux systems with Avahi, macOS, and Windows 10+.

## Option 2: Create a custom hostname
To use a simpler name like `testplatform.local` or `dts.local`:

### On YOUR machine (server):
1. Edit /etc/hosts and add:
   ```
   192.168.29.81   testplatform.local dts.local
   ```

### On OTHER devices that need to access it:
Each device needs to add to their hosts file:
- **Windows**: `C:\Windows\System32\drivers\etc\hosts`
- **macOS/Linux**: `/etc/hosts`

Add this line:
```
192.168.29.81   testplatform.local dts.local
```

## Option 3: Use a local DNS server
If you have many devices, consider setting up:
- Pi-hole
- dnsmasq
- Your router's DNS settings (if supported)

## Current Available Names:
After implementing any option, you can access your Django app at:
- `http://gss-HP-Pavilion-Notebook-15.local:8000` (should work now)
- `http://testplatform.local:8000` (after setup)
- `http://dts.local:8000` (after setup)