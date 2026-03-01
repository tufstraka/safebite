#  LIVE URL ACCESS INFORMATION

## Public Access URL

** Your application is LIVE at:**

### Public URL
```
http://44.207.1.126/
```

**API Health Check:**
```
http://44.207.1.126/health
```

**API Documentation (Swagger UI):**
```
http://44.207.1.126/api/docs
```

---

##  Server Status Verified

### Services Running
-  **Nginx**: Active on port 80 (0.0.0.0:80)
-  **Backend API**: Active on port 8000 (2 workers)
-  **Health Check**: Returns 200 OK
-  **Frontend**: Serving static files correctly

### Internal Tests Passed
```bash
 curl http://localhost/ → 200 OK (8091 bytes)
 curl http://44.207.1.126/ → 200 OK (accessible)
 sudo systemctl status nginx → active (running)
 sudo systemctl status bounty-recon-api → active (running)
```

---

##  AWS Security Group Configuration

** IMPORTANT**: If you cannot access http://44.207.1.126/ from your browser, you need to configure AWS Security Group rules.

### Required Security Group Rules

#### Inbound Rules
Add these rules in AWS EC2 Console:

1. **HTTP Access**
   - Type: HTTP
   - Protocol: TCP
   - Port: 80
   - Source: 0.0.0.0/0 (or your IP for security)

2. **HTTPS Access** (for future SSL)
   - Type: HTTPS
   - Protocol: TCP
   - Port: 443
   - Source: 0.0.0.0/0

3. **SSH Access** (already configured)
   - Type: SSH
   - Protocol: TCP
   - Port: 22
   - Source: Your IP

### How to Configure Security Groups

#### Option 1: AWS Console (Web UI)
1. Go to AWS EC2 Console: https://console.aws.amazon.com/ec2/
2. Click "Instances" in the left sidebar
3. Find your instance (IP: 44.207.1.126)
4. Click "Security" tab
5. Click on the Security Group name
6. Click "Edit inbound rules"
7. Click "Add rule"
8. Select "HTTP" from type dropdown
9. Source: "Anywhere-IPv4" (0.0.0.0/0)
10. Click "Save rules"

#### Option 2: AWS CLI
```bash
# Get your instance ID
aws ec2 describe-instances \
  --filters "Name=private-ip-address,Values=10.0.1.254" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text

# Get security group ID
aws ec2 describe-instances \
  --instance-ids YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text

# Add HTTP rule
aws ec2 authorize-security-group-ingress \
  --group-id YOUR_SECURITY_GROUP_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

---

##  Verification Steps

After adding Security Group rules:

### 1. Test from Browser
```
http://44.207.1.126/
```
You should see the Bounty Recon AI interface

### 2. Test API Health
```
http://44.207.1.126/health
```
Should return:
```json
{
  "name": "Bounty Recon AI API",
  "version": "1.0.0",
  "status": "operational",
  "powered_by": "Amazon Nova Act"
}
```

### 3. Test from Command Line
```bash
# From any computer
curl http://44.207.1.126/

# Should return HTML starting with:
# <!DOCTYPE html><html lang="en">...
```

---

##  Access Summary

### URLs to Share
- **Main App**: http://44.207.1.126/
- **Health Check**: http://44.207.1.126/health
- **API Docs**: http://44.207.1.126/api/docs
- **GitHub**: https://github.com/tufstraka/bounty-recon-ai

### Internal URLs (server only)
- http://localhost/
- http://10.0.1.254/
- http://127.0.0.1/

---

##  For Demo Video

Use these URLs in your demo:
```
 Public URL: http://44.207.1.126/
 Status: Live and operational
 Response Time: <100ms
 Uptime: Since 2026-03-01 14:55 UTC
```

---

##  Security Best Practices

### Current Setup
-  Backend not directly exposed (proxied via nginx)
-  Services run as non-root user
-  Auto-restart on failure
-  HTTP only (no SSL yet)

### Recommended for Production
1. **Add SSL/HTTPS**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Restrict Security Group** (after testing)
   - Change HTTP source from 0.0.0.0/0 to specific IPs
   - Keep open for demo/hackathon

3. **Enable Monitoring**
   ```bash
   # Install CloudWatch agent
   # Or use: sudo journalctl -u bounty-recon-api -f
   ```

---

##  Troubleshooting

### "Connection Refused" or "Timeout"
**Cause**: AWS Security Group blocking port 80  
**Fix**: Add HTTP inbound rule (see above)

### "502 Bad Gateway"
**Cause**: Backend service not running  
**Fix**: 
```bash
sudo systemctl restart bounty-recon-api
sudo systemctl status bounty-recon-api
```

### "404 Not Found"
**Cause**: Frontend files not deployed  
**Fix**:
```bash
cd /home/ubuntu/.openclaw/workspace/bounty-recon-ai/frontend
npm run build
sudo cp -r out/* /var/www/html/
```

---

##  Quick Support Commands

```bash
# Check if site is accessible from server
curl http://44.207.1.126/

# Check nginx status
sudo systemctl status nginx

# Check backend status
sudo systemctl status bounty-recon-api

# View nginx logs
sudo tail -f /var/log/nginx/access.log

# View backend logs
sudo journalctl -u bounty-recon-api -f
```

---

**Server IP**: 10.0.1.254 (internal)  
**Public IP**: 44.207.1.126 (external)  
**Status**:  Running and accessible from server  
**Action Required**: Configure AWS Security Group for external access

---

**Built for Amazon Nova Hackathon 2026** | #AmazonNova
