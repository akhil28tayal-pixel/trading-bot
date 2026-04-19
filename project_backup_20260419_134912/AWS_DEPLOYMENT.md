# AWS EC2 Deployment

This project fits best on a single Amazon EC2 Linux instance because it already uses a Python virtualenv, local files, and supervisor-managed long-running processes.

## Recommended shape

- Compute: Amazon EC2
- OS: Ubuntu 24.04 LTS
- Instance size: `t3.small` to start
- Disk: 20 GB gp3
- Time zone: `Asia/Kolkata`
- Public IP: attach an Elastic IP so the server address stays stable

## AWS setup

1. Launch an EC2 instance.
2. Create or pick an EC2 key pair for SSH access.
3. Use a security group with:
   - `22/tcp` from your IP
   - `80/tcp` from `0.0.0.0/0`
   - `443/tcp` from `0.0.0.0/0`
4. Allocate and associate an Elastic IP.
5. SSH to the instance as `ubuntu`.

## Bootstrap the instance

Upload and run the existing bootstrap script on EC2:

```bash
scp -i /path/to/key.pem deployment/deploy_to_vps.sh ubuntu@<EC2_PUBLIC_IP>:/tmp/deploy_to_vps.sh
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
sudo bash /tmp/deploy_to_vps.sh
```

That script installs system packages, creates the `trader` user, creates `/home/trader/trading_bot`, creates `.venv`, installs Python dependencies, and configures supervisor.

## Allow the `trader` user to SSH

If the bootstrap created `trader` but only `ubuntu` has your SSH key, copy the authorized key once:

```bash
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP> "sudo mkdir -p /home/trader/.ssh && sudo cp ~/.ssh/authorized_keys /home/trader/.ssh/authorized_keys && sudo chown -R trader:trader /home/trader/.ssh && sudo chmod 700 /home/trader/.ssh && sudo chmod 600 /home/trader/.ssh/authorized_keys"
```

## Deploy the app

From your local machine:

```bash
DEPLOY_HOST=<EC2_PUBLIC_IP> DEPLOY_USER=trader DEPLOY_PATH=/home/trader/trading_bot ./deploy.sh
```

The local deploy helpers now support `DEPLOY_HOST`, `DEPLOY_USER`, and `DEPLOY_PATH`, so the same scripts can target EC2 instead of the older VPS.

## Configure `.env`

Create `/home/trader/trading_bot/.env` on the server:

```dotenv
KITE_API_KEY=...
KITE_API_SECRET=...
TRADING_MODE=PAPER
PAPER_TRADING=true
TRADING_CAPITAL=100000
RISK_PER_TRADE=0.01
DAILY_LOSS_LIMIT=0.03
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

The app auto-loads `.env` at startup.

## Authenticate on EC2

The current auth flow binds to `127.0.0.1:5001`, so use SSH tunneling:

```bash
ssh -i /path/to/key.pem -L 5001:127.0.0.1:5001 trader@<EC2_PUBLIC_IP>
```

In another terminal:

```bash
ssh -i /path/to/key.pem trader@<EC2_PUBLIC_IP> "cd /home/trader/trading_bot && .venv/bin/python auth.py"
```

Then complete the Kite login through the tunneled local address.

## Start and monitor

```bash
ssh -i /path/to/key.pem trader@<EC2_PUBLIC_IP> "sudo supervisorctl start trading_bot && sudo supervisorctl status"
ssh -i /path/to/key.pem trader@<EC2_PUBLIC_IP> "tail -f /home/trader/trading_bot/logs/supervisor.log"
```

## Notes for the Telegram login feature

- Today’s auth flow is SSH-tunnel based.
- For Telegram-triggered login, the next step should be a public HTTPS callback on EC2, likely through nginx.
- Keep `80/443` available for that future step.
- Do not expose `5001` publicly.

## AWS references

- EC2 launch wizard: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-instance-wizard.html
- EC2 key pairs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
- Security groups overview: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html
- Creating security groups: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-security-group.html
- Elastic IP addresses: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html
