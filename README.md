# Oil Industry App (Groundnut, Coconut, Gingelly)

A simple Flask + SQLite app to manage products, production batches, and sales for a small oil business.

## Features
- Add products for **Groundnut**, **Coconut**, **Gingelly** oil
- Record production batches and sales
- Dashboard KPIs + simple HTML UI
- JSON health endpoint (`/health`) and summary (`/api/summary`)
- Pytest tests
- Dockerfile for containerization
- `buildspec.yml` for AWS CodeBuild to push image to ECR and deploy via CodePipeline to ECS

## Local Run
```bash
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

## Docker (Local)
```bash
docker build -t oil-industry-app:latest .
docker run -p 5000:5000 oil-industry-app:latest
```

## AWS (ECR + ECS + CodePipeline)
1. **Create ECR repo** named `oil-industry-app`.
2. **Create ECS Fargate cluster** and a service named `oil-industry-svc` (load balancer optional).
3. Create an **IAM Role** `ecsTaskExecutionRole` with AmazonECSTaskExecutionRolePolicy.
4. Update `ecs-taskdef.json` ARNs/region and register the task in ECS (or create via console).
5. **CodePipeline**:
   - Source: GitHub (this repo).
   - Build: CodeBuild (Linux, Docker privileged), use this repo's `buildspec.yml`.
   - Deploy: ECS (select your cluster + service). CodePipeline will use artifact `imagedefinitions.json` to update the service.
6. In **Parameter Store**, set `/oil-app/region` to your AWS region (e.g., `ap-south-1`).

## Environment
- `SECRET_KEY` (optional) for Flask sessions.
- `DB_PATH` (optional) to point to a persistent volume in ECS (by default uses `data.db` inside container). For production, consider RDS or EFS if you need persistence across tasks.

## Project Structure
```
.
├─ app.py
├─ requirements.txt
├─ Dockerfile
├─ buildspec.yml
├─ ecs-taskdef.json
├─ templates/
├─ static/
├─ tests/
└─ README.md
```

## Tests
```bash
pip install -r requirements.txt
pytest -q
```

## Notes
- Keep it simple: no ORM, just `sqlite3` stdlib.
- For HTTPS / domain, put an **Application Load Balancer** in front of ECS and attach an ACM certificate.
```

