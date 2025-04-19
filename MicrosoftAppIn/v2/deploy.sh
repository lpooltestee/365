#!/bin/bash
APP_NAME=assinatura
DOMAIN=assinaturas.seudominio.com
PORT=8010

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Criando serviço systemd..."
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=FastAPI - Assinatura Outlook
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which uvicorn) backend.main:app --host 0.0.0.0 --port $PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl enable $APP_NAME
sudo systemctl start $APP_NAME

echo "Configurando NGINX..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deploy concluído: http://$DOMAIN"