# Complete GitHub Runner Setup on AWS EC2

## Part 1: EC2 Instance Prerequisites

### 1.1 Launch EC2 Instance
```bash
# Use Amazon Linux 2 or Ubuntu 22.04 LTS (t3.medium or larger recommended)
# Minimum specs: 2 vCPU, 4GB RAM, 30GB storage
# Security Group: Allow inbound on ports 22 (SSH), 8080 (App)
```

### 1.2 Connect to EC2
```bash
# From your local machine
ssh -i your-key.pem ec2-user@your-ec2-public-ip
# or for Ubuntu
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Part 2: Install Required Tools on EC2

### 2.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
# or for Amazon Linux
sudo yum update -y
```

### 2.2 Install Docker
```bash
# For Ubuntu 22.04 (recommended official method):
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# For Amazon Linux 2
sudo yum install -y docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (avoid needing sudo for docker)
sudo usermod -aG docker $USER
# Apply new group permissions (important!)
newgrp docker
# Verify docker works
docker --version
```

### 2.3 Install Git
```bash
sudo apt install -y git
# or
sudo yum install -y git
```

### 2.4 Install AWS CLI
```bash
# For Ubuntu: Use official bundled installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip
sudo ./aws/install

# For Amazon Linux 2
sudo yum install -y awscli

# Verify
aws --version
```

## Part 3: Configure AWS Credentials on EC2

```bash
# Configure AWS CLI with your credentials
aws configure
# Enter:
# AWS Access Key ID: (from your secure source)
# AWS Secret Access Key: (from your secure source)
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

## Part 4: Create GitHub Runner Account & Token

### 4.1 Generate Personal Access Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `admin:org_hook` (If using organization)
4. Copy the token (you'll only see it once)

### 4.2 Get Repository URL
```bash
# Your repo URL format:
https://github.com/YOUR_USERNAME/Text-Summary-Generator
```

## Part 5: Install GitHub Actions Runner on EC2

### 5.1 Create Runner Directory
```bash
# Simple approach: use home directory (works for any user)
mkdir -p ~/github-runner
cd ~/github-runner

# Or explicit paths:
# For Ubuntu (default user 'ubuntu'):
mkdir -p /home/ubuntu/github-runner
cd /home/ubuntu/github-runner

# For Amazon Linux 2 (default user 'ec2-user'):
mkdir -p /home/ec2-user/github-runner
cd /home/ec2-user/github-runner
```

### 5.2 Download Runner Release
```bash
# Check latest version at https://github.com/actions/runner/releases
# Download (example version 2.311.0):
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf actions-runner-linux-x64.tar.gz

# Verify extraction
ls -la
# You should see: config.sh, run.sh, etc.
```

### 5.3 Run Configuration Script
```bash
# Run the config script interactively
./config.sh

# You'll be prompted for:
# 1. GitHub URL: https://github.com/YOUR_USERNAME/Text-Summary-Generator
# 2. Authentication token: (paste the token you generated above)
# 3. Runner name: (default is fine, or give it a name like "ec2-runner-1")
# 4. Runner group: (press Enter for default)
# 5. Labels: (press Enter for default, or add custom like "ec2,aws")
# 6. Work directory: (press Enter for default)
# 7. Use ephemeral: (press Enter for yes)
```

### 5.4 Install Runner as Service
```bash
# Install as systemd service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status

# To enable auto-start on boot, find the exact service name first:
sudo systemctl list-units --type=service | grep actions.runner

# Then enable the specific service (replace with your actual service name):
sudo systemctl enable actions.runner.<YOUR_SERVICE_NAME>.service

# Or use the svc.sh script which handles this automatically:
sudo ./svc.sh install  # This includes enable by default
```

## Part 6: Verify Runner is Online

### 6.1 Check GitHub Repository
1. Go to GitHub Repo → Settings → Actions → Runners
2. You should see your runner listed as "Online" (green dot)

### 6.2 View Runner Logs
```bash
# On EC2, check service logs
sudo journalctl -u actions.runner.* -f
# or
sudo tail -f /home/ec2-user/github-runner/_diag/Runner_*.log
```

## Part 7: Create .env File on EC2

```bash
# Create .env in the runner's work directory
# For Ubuntu (default user 'ubuntu'):
sudo tee /home/ubuntu/github-runner/.env > /dev/null <<'EOF'
HUGGINGFACE_USERNAME=YOUR_HF_USERNAME
HUGGINGFACE_HUB_TOKEN=<HUGGINGFACE_HUB_TOKEN>
AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
AWS_REGION=us-east-1
ECR_REPOSITORY_NAME=text-summarizer
LOG_LEVEL=INFO
EOF

# Set permissions (Ubuntu)
sudo chown ubuntu:ubuntu /home/ubuntu/github-runner/.env
sudo chmod 600 /home/ubuntu/github-runner/.env

# For Amazon Linux 2 (replace 'ubuntu' with 'ec2-user' above)
# Then change permissions for ec2-user

# Verify
cat ~/github-runner/.env
```

## Part 8: Add GitHub Secrets (Verify)

In GitHub Repo → Settings → Secrets and variables → Actions Secrets:

Ensure these secrets exist (use your actual key values when creating secrets):
- `AWS_ACCESS_KEY_ID`: <AWS_ACCESS_KEY_ID>
- `AWS_SECRET_ACCESS_KEY`: <AWS_SECRET_ACCESS_KEY>
- `AWS_REGION`: us-east-1
- `ECR_REPOSITORY_NAME`: text-summarizer

## Part 9: Create/Verify ECR Repository

```bash
# Create ECR repo if not exists
aws ecr create-repository \
  --repository-name text-summarizer \
  --region us-east-1

# Or verify existing
aws ecr describe-repositories --repository-names text-summarizer
```

## Part 10: Trigger First Workflow

### 10.1 Push Code Change
```bash
# On your local machine
cd ~/Documents/Text-Summary-Generator

# Make a small change (or just commit current state)
git add .
git commit -m "Deploy to AWS EC2 with GitHub runner"
git push origin main
```

### 10.2 Monitor Workflow
1. Go to GitHub Repo → Actions tab
2. Click on the workflow that triggered
3. Watch the build progress

**Expected steps:**
- Checkout Code ✓
- Lint code ✓
- Run unit tests ✓
- Configure AWS credentials ✓
- Login to Amazon ECR ✓
- Build, tag, and push image to ECR ✓
- Pull latest images (on EC2 runner) ✓
- Stop and remove container ✓
- Run Docker Image to serve users ✓
- Clean previous images ✓

## Part 11: Verify Deployment

### 11.1 Check Running Container
```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Check running containers
docker ps
```

### 11.2 Test the API
```bash
# Health check
curl http://localhost:8080/health
# Expected response: {"status":"healthy"}

# Predict endpoint (with sample text)
curl -X POST "http://localhost:8080/predict" \
  -H "Content-Type: application/json" \
  -d '{"text":"Alice: Hi Bob! Bob: Hello Alice, how are you?"}'
```

### 11.3 View Container Logs
```bash
# Real-time logs
docker logs -f text-summarizer

# Last 100 lines
docker logs --tail 100 text-summarizer
```

## Part 12: Troubleshooting

### Runner Won't Connect
```bash
# Check runner logs
sudo journalctl -u actions.runner.* -n 50

# Verify network connectivity
curl -I https://github.com
aws sts get-caller-identity

# Restart runner service
sudo ./svc.sh stop
sudo ./svc.sh start
```

### ECR Login Fails
```bash
# Manually authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# List ECR repos
aws ecr describe-repositories
```

### Container Won't Start
```bash
# Check image exists
docker images | grep text-summarizer

# Check container logs
docker logs text-summarizer

# Manual test
docker run -it --rm \
  --env-file /home/ec2-user/github-runner/.env \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/text-summarizer:latest \
  python app.py
```

### Port 8080 Already in Use
```bash
# Find process using port
sudo lsof -i :8080

# Kill it
sudo kill -9 <PID>

# Or use different port by modifying docker run command
docker run -d -p 8081:8080 \
  --name=text-summarizer \
  --env-file /home/ec2-user/github-runner/.env \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/text-summarizer:latest
```

### HuggingFace Token Issues
```bash
# Verify token in .env
cat /home/ec2-user/github-runner/.env | grep HUGGINGFACE

# Test HuggingFace access
docker run --rm \
  -e HUGGINGFACE_HUB_TOKEN=<HUGGINGFACE_HUB_TOKEN> \
  python:3.11 \
  python -c "from huggingface_hub import model_info; print('Token valid!')"
```

## Part 13: Maintenance

### View Runner Health
```bash
# Check runner is listening
sudo systemctl status actions.runner.*

# View logs
sudo journalctl -u actions.runner.* --no-pager | tail -50
```

### Update Runner
```bash
# Stop runner
sudo ./svc.sh stop

# Backup current version
mv /home/ec2-user/github-runner /home/ec2-user/github-runner-backup

# Download and install new version (repeat Part 5.2-5.4)

# Start new version
sudo ./svc.sh start
```

### Cleanup Old Docker Images
```bash
# Remove all stopped containers
docker container prune -f

# Remove all dangling images
docker image prune -f

# Remove images older than 30 days
docker image prune -a --filter "until=720h"
```

## Part 14: Production Best Practices

### Security
```bash
# Restrict EC2 security group to your IP only
# SSH only from your IP
# 8080 only if you need remote access

# Rotate credentials regularly
# Never commit .env to git
# Use EC2 IAM roles instead of hardcoded keys (advanced)
```

### Monitoring
```bash
# Setup CloudWatch logs
# Monitor disk space: df -h
# Monitor memory: free -h
# Monitor CPU: top

# Check runner uptime
uptime

# Check disk usage
du -sh /home/ec2-user/github-runner
```

### Auto-cleanup (Optional)
```bash
# Add cron job to clean Docker regularly
crontab -e

# Add this line:
0 2 * * * docker system prune -af --filter "until=720h"
```

## Summary Checklist

- [ ] EC2 instance launched with proper security groups
- [ ] Docker installed and running
- [ ] GitHub runner downloaded and extracted
- [ ] Runner configured and registered with GitHub
- [ ] Runner service installed and started
- [ ] Runner appears as "Online" in GitHub Settings
- [ ] .env file created on EC2 with all credentials (placeholders shown)
- [ ] ECR repository created
- [ ] AWS credentials configured on EC2
- [ ] Code pushed to trigger workflow
- [ ] Workflow completed successfully
- [ ] Container running on EC2
- [ ] API endpoints responding (health, predict)
- [ ] Application logs viewable and clean

## Quick Commands Reference

```bash
# SSH to EC2
ssh -i key.pem ec2-user@ip

# Check runner status
sudo systemctl status actions.runner.*

# View runner logs
sudo journalctl -u actions.runner.* -f

# Check running container
docker ps

# View app logs
docker logs -f text-summarizer

# Test API
curl http://localhost:8080/health

# Restart container
docker restart text-summarizer

# Stop runner
sudo ./svc.sh stop

# Start runner
sudo ./svc.sh start
```
