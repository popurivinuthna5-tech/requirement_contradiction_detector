# AWS EC2 Production Deployment Guide

This guide walks you through deploying the **Requirement Conflict & Overlap Analyzer** to an **AWS EC2** Linux instance for production use.

---

## 1. Prerequisites & AWS Architecture

- **AWS Account** with permissions to launch EC2 instances and configure Security Groups.
- **Recommended Instance Type:** `t3.small` (2 vCPU, 2 GB RAM) or `t3.medium` (2 vCPU, 4 GB RAM).
- **Recommended OS:** Ubuntu 22.04 LTS, Ubuntu 24.04 LTS, or Amazon Linux 2023.
- **Storage:** 20 GB gp3 SSD.

---

## 2. Launching the EC2 Instance

1. Navigate to the **AWS Management Console** -> **EC2** -> **Launch Instance**.
2. **Name:** `requirement-conflict-analyzer-prod`
3. **Application and OS Images:** Select **Ubuntu Server 24.04 LTS** (or Amazon Linux 2023).
4. **Instance Type:** `t3.small` or `t3.medium`.
5. **Key Pair:** Select or create your `.pem` SSH key pair (e.g. `req-analyzer-key.pem`).
6. **Network & Security Group Settings:**
   Configure Security Group inbound rules:
   | Type | Protocol | Port Range | Source | Purpose |
   | :--- | :--- | :--- | :--- | :--- |
   | **SSH** | TCP | `22` | `My IP` (or `0.0.0.0/0`) | Secure Shell Access |
   | **HTTP** | TCP | `80` | `0.0.0.0/0` | Public Web Traffic (Nginx) |
   | **HTTPS** | TCP | `443` | `0.0.0.0/0` | SSL/TLS Encrypted Traffic |
   | **Custom TCP** | TCP | `8000` | `0.0.0.0/0` (Optional) | Direct Backend API access |
7. **Storage:** 20 GB `gp3`.
8. Click **Launch Instance**.

---

## 3. Connecting to the Instance

From your local terminal:

```bash
chmod 400 req-analyzer-key.pem
ssh -i req-analyzer-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

*(Note: If using Amazon Linux 2023, username is `ec2-user` instead of `ubuntu`)*.

---

## 4. Deploying the Application

### Option A: Automated One-Click Script (Recommended)

1. Clone or copy your project files into `/home/ubuntu/requirement-analyzer`:

```bash
cd /home/ubuntu
git clone <YOUR_REPOSITORY_URL> requirement-analyzer
# OR upload using SCP:
# scp -i req-analyzer-key.pem -r requirement_contradiction_dector/* ubuntu@<YOUR_EC2_PUBLIC_IP>:/home/ubuntu/requirement-analyzer/
```

2. Make the deployment script executable and run it:

```bash
cd /home/ubuntu/requirement-analyzer
chmod +x deployment/deploy_ec2.sh
bash deployment/deploy_ec2.sh
```

The script automatically:
- Installs Python 3, pip, venv, Nginx, and build libraries
- Sets up Python virtual environment and installs all dependencies
- Generates sample test documents (`.pdf`, `.docx`, `.txt`)
- Configures and starts the `requirement-analyzer` systemd service
- Configures and restarts Nginx as a reverse proxy on Port 80
- Verifies health check and displays public IP URL!

---

### Option B: Docker & Docker Compose Deployment

If you prefer containerized deployment:

1. Install Docker and Docker Compose on EC2:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker
```

2. Build and start containers:
```bash
cd /home/ubuntu/requirement-analyzer/deployment
docker-compose up -d --build
```

3. Check container status:
```bash
docker ps
docker logs req-conflict-analyzer -f
```

---

## 5. Domain Configuration and HTTPS (SSL)

To attach a custom domain and configure HTTPS with Let's Encrypt:

1. **Point your DNS A-Record:**
   Point `requirements.yourcompany.com` to your EC2 Public Elastic IP.

2. **Install Certbot:**
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

3. **Obtain and Install SSL Certificate:**
```bash
sudo certbot --nginx -d requirements.yourcompany.com
```

4. Certbot automatically modifies `/etc/nginx/sites-available/requirement-analyzer` to redirect HTTP traffic to HTTPS (port 443) with auto-renewing certificates!

---

## 6. Process Monitoring & Maintenance

### Check Service Status
```bash
sudo systemctl status requirement-analyzer
```

### View Live Application Logs
```bash
sudo journalctl -u requirement-analyzer -f
```

### Restart Application Service
```bash
sudo systemctl restart requirement-analyzer
```

### Reload Nginx Configuration
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 7. Verifying Deployment

Open your browser and navigate to:

`http://<YOUR_EC2_PUBLIC_IP>` or `https://requirements.yourcompany.com`

1. The **Authentication Screen** will appear.
2. Click **"Try Interactive Demo Workspace"** (or log in via Google/Apple).
3. The **Dashboard** will load with live telemetry cards, charts, and detected conflicts.
4. Open the **Documents** tab and test uploading a PDF or DOCX file.
5. Open the **Conflict Analysis** tab and click **Inspect** on any conflict to test the Side-by-Side Comparison Modal.
6. Open the **Conflict Reports** tab and test exporting CSV, JSON, and Markdown reports.
