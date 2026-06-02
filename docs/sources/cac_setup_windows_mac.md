# CAC Setup — Windows and Mac

Public-source reference for SMCR members setting up Common Access Card (CAC) authentication on a personal or government-issued computer.
All downloads below are from militarycac.com (maintained by retired Army CW4 Michael Danberry) or official DoD sources.

**Bookmark:** https://www.militarycac.com — check here first whenever something stops working; cert updates and OS changes break things regularly and the site stays current.

---

## Primary Sources

- Title: MilitaryCAC — Windows CAC Setup
- Type: Public reference site
- Category: CAC / PKI / IT setup
- Official URL: https://www.militarycac.com
- Classification label: UNCLASSIFIED
- CUI flag: false

- Title: DoD Cyber Exchange — InstallRoot
- Type: Official DoD PKI tool
- Category: CAC / PKI / IT setup
- Official URL: https://dl.dod.cyber.mil/wp-content/uploads/pki-pke/msi/InstallRoot_5.6x32_NonAdmin.msi
- Classification label: UNCLASSIFIED
- CUI flag: false

---

## Windows Setup

### Who this applies to
Windows 10 and Windows 11. No ActivClient required for most users — Windows has built-in smart card support. If your unit S-6 requires ActivClient, obtain it through them (requires a CAC to download from DISA).

### Step 1 — Install DoD Certificates

Pick one of the following. InstallRoot is the easiest — it automates everything.

| Option | Download | Size | Notes |
|--------|----------|------|-------|
| InstallRoot 5.6 (MSI) | https://militarycac.com/CACDrivers/InstallRoot_5.6x32_NonAdmin.msi | 27.7 MB | **Recommended.** Run, click "Install DoD Certificates." Done. |
| InstallRoot 5.6 (ZIP) | https://militarycac.com/CACDrivers/InstallRoot_5.6x32_NonAdmin.zip | 25.9 MB | Use if MSI is blocked by group policy. Extract, run the .exe inside. |
| HomeUserCertTool V06 | https://militarycac.com/CACDrivers/HomeUserCertTool_V06.zip | 3.3 MB | Bundled — includes InstallRoot + Cross Certificate Removal tool. Good for personal machines with cert conflicts. |

**What InstallRoot installs:** DoD Root CA 3, 4, 5, 6 and all intermediate CAs (DoD ID CA, Email CA, SW CA, Derility CA series). Without these, CAC-protected .mil sites show certificate errors and refuse to load.

After running, reboot.

### Step 2 — Plug in your CAC reader

Windows 10/11 recognizes most USB CAC readers automatically. If your reader is not recognized:
- Unplug, wait 10 seconds, replug
- Check Device Manager for "Unknown Device" — if present, install the reader manufacturer's driver (usually SCR or HID brand)
- Gemalto/Thales, SCR-3500A, and most HID readers are plug-and-play

### Step 3 — Browser

| Browser | Works? | Notes |
|---------|--------|-------|
| **Microsoft Edge** | ✅ Best | Native CAC support. Recommended for all CAC-protected sites. |
| **Chrome** | ✅ Good | Works natively on Windows. No extensions needed. |
| **Firefox** | ⚠️ Painful | Requires manual PKCS#11 module configuration. Avoid unless required. |
| **Internet Explorer** | ❌ Dead | Deprecated. Do not use. |

### Step 4 — Test

Go to https://www.dmdc.osd.mil/appj/dwp/index.do (DMDC self-service). If your CAC is recognized and you can authenticate, setup is complete.

### Common Windows Problems

| Problem | Fix |
|---------|-----|
| "No certificates found" | Run InstallRoot again; reboot; try a different USB port |
| CAC reader not recognized | Unplug/replug; update Windows; try a different port or cable |
| Certificate errors on .mil sites | Certs not installed — run InstallRoot |
| "Can't connect to this page" on .mil sites | Edge/Chrome; disable VPN temporarily to test |
| PIN prompt doesn't appear | Ensure Smart Card service is running: `services.msc` → Smart Card → set to Automatic and Start |

---

## Mac Setup

### Who this applies to
macOS Sierra (10.12) and newer. Modern macOS has native smart card support built in — no middleware required. Older than Sierra (El Capitan and below): see https://www.militarycac.com/cacenablers.htm for middleware options.

### Step 1 — Install DoD Certificates

Download each file and **double-click** it to open Keychain Access and install. Start with AllCerts.p7b — it installs the full bundle in one shot.

| File | URL | Updated | Notes |
|------|-----|---------|-------|
| **AllCerts.p7b** | https://militarycac.com/maccerts/AllCerts.p7b | 21 Jan 2026 | **Start here.** Installs all DoD root + intermediate CAs at once. |
| RootCert3.cer | https://militarycac.com/maccerts/RootCert3.cer | Nov 2015 | Install if AllCerts misses it |
| RootCert4.cer | https://militarycac.com/maccerts/RootCert4.cer | May 2016 | Install if AllCerts misses it |
| RootCert5.cer | https://militarycac.com/maccerts/RootCert5.cer | Nov 2017 | Install if AllCerts misses it |
| RootCert6.cer | https://militarycac.com/maccerts/RootCert6.cer | Mar 2023 | Install if AllCerts misses it |
| AllCerts.zip | https://militarycac.com/maccerts/AllCerts.zip | — | Firefox users only — 45+ individual .cer files for manual import |

After installing AllCerts.p7b, verify in **Keychain Access → System → Certificates** that "DoD Root CA 3," "DoD Root CA 5," and "DoD Root CA 6" appear and show as trusted (blue checkbox, not red X).

### Step 2 — Plug in your CAC reader

Modern macOS recognizes most USB CAC readers without drivers. If yours is not recognized:
- Unplug, wait 10 seconds, replug
- If using an SCR-3500A and it still fails: download `scmccid_mac_5.0.41.zip` from the MilitaryCAC reader page and install the driver manually

### Step 3 — Verify smart card detection

Open **Terminal** and run:
```
system_profiler SPSmartCardsDataType
```
If your CAC is inserted and detected, you'll see card details. If nothing appears, the reader isn't communicating — try a different USB port or cable.

### Step 4 — Browser

| Browser | Works? | Notes |
|---------|--------|-------|
| **Safari** | ✅ Best | Native CAC support on Mac. Recommended. |
| **Chrome** | ✅ Good | Works natively. No extensions needed. |
| **Firefox** | ⚠️ Painful | Requires AllCerts.zip manual import + PKCS#11 module setup. Avoid. |

### Step 5 — Test

Go to https://www.dmdc.osd.mil/appj/dwp/index.do. CAC PIN prompt should appear automatically in your browser.

### Common Mac Problems

| Problem | Fix |
|---------|-----|
| Certificate errors on .mil sites | AllCerts.p7b not installed or certs not trusted — reinstall and check Keychain Access |
| CAC reader not recognized | Unplug/replug; try different port; SCR-3500A may need manual driver |
| "No valid certificates" in browser | Open Keychain Access; confirm DoD Root CA certs show as trusted; try restarting the browser |
| Keychain keeps prompting for password | Normal on first use per session — macOS is protecting your CAC certs |
| Safari not prompting for CAC | Restart Safari; try inserting CAC before opening the browser |

---

## Recommendations for SMCR Units

1. **Push InstallRoot to all members before AT.** DoD cert install is the single most common failure point. A unit-wide email with the direct MSI link prevents half the helpdesk calls.

2. **Keep this link handy:** https://www.militarycac.com — bookmark it in unit SharePoint, Teams, or wherever your members will find it.

3. **Browser standardization:** Recommend Edge on Windows, Safari or Chrome on Mac. Eliminates 90% of browser-related CAC issues.

4. **Do not troubleshoot without knowing the OS and browser first.** Most CAC problems are environment-specific. "It doesn't work" is not enough to help.

5. **Certificate expiration:** DoD rotates certs periodically. If members report sudden cert errors across the unit, check militarycac.com — there's likely a new AllCerts bundle. Re-running InstallRoot or re-downloading AllCerts.p7b fixes it.

6. **ActivClient:** Only install if explicitly required by your unit S-6 or a specific application (AHLTA, IPPS-A edge cases). It is not needed for web-based CAC auth on modern Windows.

---

## Expected Uses

- Admin agent and S-6 agent expansion: CAC troubleshooting workflows
- Pre-drill readiness checks: confirm members have valid certs before drill weekend
- New member onboarding checklists
- IT support reference for unit S-6

## Notes

Do not store member-specific CAC certificate information, PINs, or PKI private key material anywhere in this system. This document covers only the public setup process using publicly available tools and certificates.
