# EC2 Setup Guide for Text Summarization API

## Prerequisites
- EC2 instance running Ubuntu 22.04+ with security group allowing SSH (22), HTTP (80), HTTPS (443), and custom port 8080
- GitHub runner installed and configured on EC2

## Step 1: Install GitHub Runner on EC2

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Create a directory for the runner
mkdir -p /home/ec2-user/github-runner
cd /home/ec2-user/github-runner

# Download the latest runner release
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf actions-runner-linux-x64.tar.gz

# Run configuration script
./config.sh --url https://github.com/YOUR_GITHUB_USERNAME/Text-Summary-Generator --token YOUR_GITHUB_TOKEN

# Install as service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start
```

## Step 2: Install Docker & AWS CLI

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker ec2-user
sudo systemctl start docker
sudo systemctl enable docker

# Install AWS CLI
sudo apt install -y awscli

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID and Secret Access Key
```

## Step 3: Create .env File on EC2

```bash
# Create .env in ec2-user home directory
sudo tee /home/ec2-user/.env > /dev/null <<EOF
HUGGINGFACE_USERNAME=your_huggingface_username
HUGGINGFACE_HUB_TOKEN=your_huggingface_api_token
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_REGION=us-east-1
LOG_LEVEL=INFO
EOF

# Set proper permissions
sudo chown ec2-user:ec2-user /home/ec2-user/.env
sudo chmod 600 /home/ec2-user/.env
```

## Step 4: Get HuggingFace Credentials

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Read" access
3. Copy the token and set in `.env`:

```bash
HUGGINGFACE_USERNAME=your_username
HUGGINGFACE_HUB_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

## Step 5: GitHub Secrets (Already Added)

Your secrets in GitHub Settings → Secrets and variables:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_REGION` - us-east-1 (or your region)
- `ECR_REPOSITORY_NAME` - text-summarizer (or your repo name)

## Step 6: Verify EC2 Runner Connection

Check if your runner is connected:
```bash
# On EC2
cd /home/ec2-user/github-runner
./run.sh
```

In GitHub repo → Settings → Actions → Runners, you should see your EC2 instance listed as "Online"

## Step 7: Deploy & Test

Push to main branch to trigger the workflow:
```bash
git add .
git commit -m "Deploy to AWS EC2"
git push origin main
```

Monitor the deployment:
1. Go to GitHub repo → Actions
2. Watch the workflow execute
3. Check your EC2 instance:

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Check running containers
docker ps

# View logs
docker logs text-summarizer

# Test the API
curl -X GET http://localhost:8080/health
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Alice: Hi Bob, how are you? Bob: I am doing great!"}'
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs text-summarizer

# Remove old container and retry
docker rm -f text-summarizer
```

### ECR login fails
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### HuggingFace token issues
```bash
# Verify .env is readable by docker
cat /home/ec2-user/.env
# Make sure permissions are correct
sudo chmod 600 /home/ec2-user/.env
```

### Port 8080 already in use
```bash
# Find and kill process using port 8080
sudo lsof -i :8080
sudo kill -9 <PID>
```

## Security Considerations

1. **Restrict security group**: Only allow HTTP/HTTPS and SSH from your IP
2. **Use IAM roles**: Instead of access keys, consider EC2 IAM roles
3. **Rotate tokens**: Regularly rotate HuggingFace tokens and AWS credentials
4. **Secure .env**: Never commit `.env` to git, use `.gitignore`

## Monitoring

```bash
# Check container health
docker ps
docker stats text-summarizer

# Check API endpoints
curl http://localhost:8080/health

# View application logs
docker logs -f text-summarizer
```
