# AI-Powered Outage Analysis Setup

The dashboard now includes AI-powered analysis for property-wide outages using Claude AI.

## Quick Setup

1. **Get your Anthropic API key**
   - Visit: https://console.anthropic.com/settings/keys
   - Create a new API key or use an existing one

2. **Create .env file**
   ```bash
   cp .env.example .env
   ```

3. **Add your API key to .env**
   ```bash
   nano .env
   # or
   vi .env
   ```

   Replace `your-api-key-here` with your actual API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
   ```

4. **Restart the API server**
   ```bash
   ./start_api_server.sh
   ```

   Or manually:
   ```bash
   # Load environment variables
   export $(grep -v '^#' .env | xargs)

   # Restart server
   pkill -f api_server.py
   nohup ./venv/bin/python3 api_server.py > logs/api_server.log 2>&1 &
   ```

## How It Works

When you view a property detail page:

1. **Detection**: System automatically detects property-wide outages (>80% of networks affected in any hour within last 24 hours)

2. **Analysis**: If detected, Claude AI analyzes:
   - Timing patterns (simultaneous vs cascading failures)
   - Equipment correlations (shared XPON/7x50 routers)
   - Geographic patterns (location clustering)
   - Performance data (degradation before failure)

3. **Display**: Analysis appears at the top of the property page with:
   - Root cause hypotheses (ranked by likelihood)
   - Supporting and contradicting evidence
   - Alternative theories
   - Recommendations for investigation/prevention
   - Model name that generated the analysis

## Troubleshooting

### Error: "AI analysis unavailable"

**Cause**: ANTHROPIC_API_KEY environment variable not set

**Solution**:
1. Check if .env file exists: `ls -la .env`
2. Check if key is set: `echo $ANTHROPIC_API_KEY`
3. If empty, follow setup steps above
4. Restart API server with: `./start_api_server.sh`

### Check API server logs

```bash
tail -f logs/api_server.log
```

### Verify API key is loaded

```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# Should output your API key (sk-ant-api03-...)
# If empty, the environment variable is not set
```

## Cost Information

- Model used: **claude-sonnet-4-20250514**
- Typical analysis: ~2,000-4,000 tokens per request
- Only triggers on property-wide outages (>80% networks affected)
- Each property page view with property-wide outage = 1 API call

## Example Analysis Output

The AI examines patterns to theorize root causes:

- **Simultaneous failures** → Upstream equipment failure or power outage
- **Sequential/cascading** → Network propagation or overload issue
- **Geographic clustering** → Fiber cut or localized infrastructure issue
- **Equipment correlation** → Specific XPON/7x50 router failure
- **Performance degradation** → Congestion or capacity issue

Analysis includes specific data references and actionable recommendations.
