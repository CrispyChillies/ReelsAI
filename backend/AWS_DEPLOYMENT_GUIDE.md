# AWS Elastic Beanstalk Deployment Guide for ReelsAI Backend

## Overview
This guide will help you deploy the ReelsAI Django backend to AWS Elastic Beanstalk, which provides automatic scaling, load balancing, and easy management for your application.

## Prerequisites

1. **AWS Account**: Sign up at [aws.amazon.com](https://aws.amazon.com)
2. **AWS CLI**: Install from [aws.amazon.com/cli](https://aws.amazon.com/cli/)
3. **EB CLI**: Install using `pip install awsebcli`
4. **Git**: Ensure your code is in a git repository

## Step 1: Install AWS EB CLI

```bash
pip install awsebcli
```

Verify installation:
```bash
eb --version
```

## Step 2: Configure AWS Credentials

Run AWS configure to set up your credentials:
```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`, `ap-southeast-1`)
- Default output format: `json`

Get these from AWS Console → IAM → Users → Security Credentials

## Step 3: Initialize Elastic Beanstalk

Navigate to your backend directory and initialize EB:

```bash
cd backend
eb init
```

Follow the prompts:
1. **Select region**: Choose closest to your users (e.g., `ap-southeast-1` for Singapore)
2. **Application name**: `reelsai-backend` (or your preferred name)
3. **Platform**: Select `Python`
4. **Platform version**: Choose Python 3.11 or 3.12
5. **CodeCommit**: No (unless you want to use it)
6. **SSH**: Yes (for debugging)

This creates `.elasticbeanstalk/config.yml` in your project.

## Step 4: Create Environment Variables File

Create `.ebextensions/04_environment.config` for non-sensitive defaults:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
    DEBUG: "False"
```

**Important**: Never commit sensitive values like API keys or passwords!

## Step 5: Configure Environment Variables in AWS

You'll set sensitive environment variables through AWS Console or EB CLI:

### Using EB CLI:
```bash
eb setenv DEBUG=False \
  SECRET_KEY="your-production-secret-key" \
  ALLOWED_HOSTS="your-app.elasticbeanstalk.com" \
  DB_HOST="aws-1-ap-southeast-1.pooler.supabase.com" \
  DB_NAME="postgres" \
  DB_USER="postgres.oacnymbkhkxwlnzeyrll" \
  DB_PASSWORD="your-db-password" \
  DB_PORT="6543" \
  DB_SSLMODE="require" \
  OPENAI_API_KEY="your-openai-key" \
  GEMINI_API_KEY="your-gemini-key" \
  NEO4J_URI="your-neo4j-uri" \
  NEO4J_USERNAME="neo4j" \
  NEO4J_PASSWORD="your-neo4j-password" \
  ZILLIZ_URI="your-zilliz-uri" \
  ZILLIZ_TOKEN="your-zilliz-token" \
  COLLECTION_NAME="user_saved_items_embeddings" \
  SUPABASE_URL="https://oacnymbkhkxwlnzeyrll.supabase.co/" \
  SUPABASE_KEY="your-supabase-key" \
  RABBITMQ_HOST="your-rabbitmq-host" \
  RABBITMQ_PORT="5672" \
  CORS_ALLOWED_ORIGINS="https://your-frontend.vercel.app" \
  BACKEND_BASE_URL="https://your-app.elasticbeanstalk.com" \
  FRONTEND_BASE_URL="https://your-frontend.vercel.app"
```

### Using AWS Console:
1. Go to Elastic Beanstalk console
2. Select your environment
3. Configuration → Software → Edit
4. Add all environment variables in the "Environment properties" section

## Step 6: Create the Environment

Create your first environment:

```bash
eb create reelsai-production
```

Or specify options:
```bash
eb create reelsai-production \
  --platform "python-3.11" \
  --instance-type t3.medium \
  --envvars DEBUG=False
```

This will:
- Create EC2 instances
- Set up load balancer
- Configure security groups
- Deploy your application
- Run migrations (via container_commands)

Wait for deployment (5-10 minutes).

## Step 7: Deploy Updates

After making code changes:

```bash
# Commit your changes
git add .
git commit -m "Update feature"

# Deploy to EB
eb deploy
```

## Step 8: Configure HTTPS (SSL/TLS)

### Option A: Use AWS Certificate Manager (Free SSL)

1. **Request Certificate**:
   - Go to AWS Certificate Manager
   - Request a public certificate
   - Enter your domain (e.g., `api.reelsai.com`)
   - Validate via DNS or Email

2. **Configure Load Balancer**:
   ```bash
   eb console
   ```
   - Go to Configuration → Load Balancer
   - Add listener on port 443 (HTTPS)
   - Select your SSL certificate
   - Set security policy

3. **Update DNS**:
   - Point your domain to the EB load balancer URL

### Option B: Use Let's Encrypt (Free)

Create `.ebextensions/05_https.config`:
```yaml
packages:
  yum:
    mod24_ssl: []

files:
  /etc/httpd/conf.d/ssl_rewrite.conf:
    mode: "000644"
    owner: root
    group: root
    content: |
      RewriteEngine On
      RewriteCond %{HTTP:X-Forwarded-Proto} !https
      RewriteRule ^.*$ https://%{HTTP_HOST}%{REQUEST_URI} [R,L]
```

## Step 9: Set Up RabbitMQ (for Video Processing)

### Option A: AWS MQ (Managed RabbitMQ)
1. Go to Amazon MQ console
2. Create broker (RabbitMQ)
3. Choose instance type (mq.t3.micro for dev)
4. Update `RABBITMQ_HOST` and credentials in EB environment variables

### Option B: External Service (CloudAMQP)
1. Sign up at [cloudamqp.com](https://www.cloudamqp.com/)
2. Create free or paid plan
3. Get connection details
4. Update environment variables

## Step 10: Configure Worker for Background Tasks

Create a separate worker environment for RabbitMQ consumer:

```bash
eb create reelsai-worker --tier worker
```

Or run worker as a background process in your web environment by creating `.ebextensions/06_worker.config`:

```yaml
container_commands:
  04_start_worker:
    command: "source /var/app/venv/*/bin/activate && nohup python manage.py run_video_worker > /var/log/worker.log 2>&1 &"
    leader_only: true
```

## Step 11: Monitoring and Logs

### View logs:
```bash
# Recent logs
eb logs

# Follow logs in real-time
eb ssh
sudo tail -f /var/log/eb-engine.log
sudo tail -f /var/log/web.stdout.log
```

### CloudWatch:
- Elastic Beanstalk automatically sends logs to CloudWatch
- Set up alarms for errors and performance

## Step 12: Database Migrations

Migrations run automatically via `.ebextensions/03_django.config`.

To run manually:
```bash
eb ssh
source /var/app/venv/*/bin/activate
cd /var/app/current
python manage.py migrate
python manage.py createsuperuser
```

## Step 13: Scaling Configuration

### Auto Scaling:
```bash
eb console
```
- Configuration → Capacity
- Environment type: Load balanced
- Min instances: 1
- Max instances: 4
- Scaling triggers: Based on CPU, Network, or custom metrics

### Instance Type:
- Development: `t3.micro` or `t3.small` (free tier eligible)
- Production: `t3.medium` or `t3.large`
- High load: `c5.large` or higher

## Common Commands

```bash
# Check status
eb status

# Open application in browser
eb open

# View environment info
eb console

# SSH into instance
eb ssh

# View/download logs
eb logs
eb logs --all

# Terminate environment (CAREFUL!)
eb terminate reelsai-production
```

## Cost Estimation

- **t3.micro** (free tier): Free for first year, then ~$7/month
- **t3.medium**: ~$30/month
- **Load Balancer**: ~$16/month
- **Data Transfer**: Variable based on usage
- **RDS (if used)**: ~$15-50/month depending on size

**Note**: Supabase (external) costs are separate.

## Troubleshooting

### Application won't start:
```bash
eb logs
# Check for Python errors, missing dependencies, environment variable issues
```

### Database connection issues:
- Verify DB environment variables
- Check security group allows outbound connections to Supabase
- Test connection: `eb ssh` then `python manage.py dbshell`

### Static files not loading:
```bash
eb ssh
source /var/app/venv/*/bin/activate
cd /var/app/current
python manage.py collectstatic --noinput
```

### Memory issues:
- Upgrade instance type
- Reduce worker threads in Procfile
- Check for memory leaks

## Alternative: Deploy with Docker (Advanced)

If you prefer Docker, create `Dockerrun.aws.json` and deploy containerized application.

## Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Enable HTTPS**: Always use SSL in production
3. **Set DEBUG=False**: Never run debug mode in production
4. **Restrict ALLOWED_HOSTS**: Only allow your domain
5. **Use IAM roles**: Don't hardcode AWS credentials
6. **Regular updates**: Keep dependencies updated
7. **Enable WAF**: Use AWS Web Application Firewall for DDoS protection
8. **Database backups**: Configure automated backups in Supabase

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up database backups
- [ ] Configure CloudWatch alarms
- [ ] Set up auto-scaling
- [ ] Configure logging and monitoring
- [ ] Test all API endpoints
- [ ] Set up CI/CD pipeline (optional)
- [ ] Document environment variables
- [ ] Configure RabbitMQ for workers
- [ ] Test video processing pipeline

## Next Steps

1. Deploy to staging environment first
2. Run comprehensive tests
3. Set up CI/CD with GitHub Actions or AWS CodePipeline
4. Configure custom domain
5. Set up monitoring and alerting
6. Plan backup and disaster recovery

## Support Resources

- [AWS Elastic Beanstalk Docs](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [AWS Free Tier](https://aws.amazon.com/free/)

---

**Ready to deploy?** Start with Step 1 and follow through sequentially. Good luck! 🚀
