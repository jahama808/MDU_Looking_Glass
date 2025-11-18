# Configuration Guide

## Environment Configuration (.env file)

The application uses a `.env` file for configuration. This file contains sensitive credentials and should **never be committed to version control**.

### Setup

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your credentials**:
   ```bash
   nano .env  # or use your preferred editor
   ```

### Configuration Options

#### Anthropic API (AI-powered outage analysis)

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

- **Purpose**: Enables AI-powered analysis of network outages
- **Get your key**: [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
- **Optional**: The system works without this, but AI analysis will be disabled

#### Pushover Notifications

```bash
PUSHOVER_USER_KEY=your-pushover-user-key-here
PUSHOVER_API_TOKEN=your-pushover-api-token-here
```

- **Purpose**: Enables push notifications to your phone for:
  - Eero data downloads (start, complete, errors)
  - Data processing (start, complete, errors)
  - Property-wide outages detected (≥75% networks down)

- **Get credentials**:
  1. Sign up at [pushover.net](https://pushover.net/)
  2. **User Key**: Found on your dashboard after login (30 characters)
  3. **API Token**: Create an app at [pushover.net/apps/build](https://pushover.net/apps/build) (30 characters)

- **Optional**: The system works without this, but you won't receive notifications

### Example .env File

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-abc123...

# Pushover Notification Configuration
PUSHOVER_USER_KEY=u7m52kv3izu2tcw2p8zeg5ubz5ps8b
PUSHOVER_API_TOKEN=yan763iw8x9kbcqymo7k3am4z3y7vdy
```

## Security Best Practices

1. **Never commit `.env` to git**
   - The `.gitignore` file should already exclude `.env`
   - Verify: `git check-ignore .env` should return `.env`

2. **Use `.env.example` for documentation**
   - Keep `.env.example` updated with all configuration options
   - Use placeholder values, never real credentials
   - This file IS committed to version control

3. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

4. **Rotate credentials periodically**
   - Change API keys every 3-6 months
   - Immediately rotate if potentially exposed

## Verification

### Check if .env is loaded

Run the test scripts:

```bash
# Test Pushover configuration
venv/bin/python pushover_notifier.py

# Expected output if configured:
# "Pushover notification sent: Test Notification"

# Expected output if NOT configured:
# "Warning: Pushover credentials not configured"
```

### Check environment variables manually

```bash
venv/bin/python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Pushover User:', os.getenv('PUSHOVER_USER_KEY')[:10] + '...' if os.getenv('PUSHOVER_USER_KEY') else 'Not set')"
```

## Troubleshooting

### .env file not loading

1. **Check file location**: Must be in project root directory
   ```bash
   ls -la .env
   ```

2. **Check file format**: No spaces around `=`, no quotes needed
   ```bash
   # Correct
   PUSHOVER_USER_KEY=abc123def456

   # Incorrect
   PUSHOVER_USER_KEY = abc123def456
   export PUSHOVER_USER_KEY="abc123def456"
   ```

3. **Install python-dotenv**:
   ```bash
   venv/bin/pip install python-dotenv
   ```

### Pushover notifications not working

1. **Verify credentials format**:
   - User Key: 30 characters (lowercase letters and numbers)
   - API Token: 30 characters (lowercase letters and numbers)

2. **Test credentials** at [pushover.net/api](https://pushover.net/api)

3. **Check API response**:
   - Run `venv/bin/python pushover_notifier.py` for detailed error messages

4. **Common errors**:
   - `application token is invalid`: Wrong API token
   - `user key is invalid`: Wrong user key
   - `no active devices`: Install Pushover app on your phone

## Alternative: Environment Variables

If you prefer not to use a `.env` file, you can set environment variables directly:

### Linux/macOS (in ~/.bashrc or ~/.zshrc):
```bash
export ANTHROPIC_API_KEY="your-key-here"
export PUSHOVER_USER_KEY="your-user-key"
export PUSHOVER_API_TOKEN="your-api-token"
```

### Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
$env:PUSHOVER_USER_KEY="your-user-key"
$env:PUSHOVER_API_TOKEN="your-api-token"
```

## Dependencies

The application automatically loads `.env` using `python-dotenv`:

```bash
venv/bin/pip install -r requirements.txt
```

This installs:
- `python-dotenv>=1.0.0` - Load environment variables from .env
- All other required packages

---

**Need more help?** See:
- [PUSHOVER_SETUP.md](PUSHOVER_SETUP.md) - Detailed Pushover setup guide
- [PUSHOVER_README.md](PUSHOVER_README.md) - Quick start for Pushover
