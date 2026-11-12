# HTTPS estable y arranque de MAX

Desde MAX 0.1.2 hay dos opciones de entrada estable. Si no tienes un dominio
administrado en Cloudflare, utiliza [Workers HTTPS](WORKERS-HTTPS.md): una URL
`workers.dev` fija con registro autenticado del conector al arrancar Linux.
La guía de esta página describe la alternativa de túnel con nombre y dominio.
Elige una de las dos; no es necesario mantener ambos conectores ejecutándose.

La alternativa con dominio utiliza un túnel con nombre y un registro DNS permanente. La URL no
depende de la IP de la laptop ni cambia al reiniciar el proceso. Requiere un
dominio administrado en Cloudflare, conectividad a Internet y la laptop encendida.
Los ejemplos usan `max.example.com`; sustituye el hostname en la configuración
privada. No publiques credenciales ni identificadores de tu instalación.

## Túnel dedicado

Instala la versión oficial de `cloudflared` indicada en `deploy/versions.json`
y verifica su SHA-256. Su ruta esperada es `~/.local/bin/cloudflared`.

Con una cuenta autorizada para el dominio, crea un túnel dedicado. Usa una
configuración de bootstrap vacía para no heredar túneles de otras aplicaciones:

```bash
install -d -m 700 ~/.config/max ~/.local/share/max
printf '{}\n' > ~/.config/max/cloudflared-bootstrap.yml
chmod 600 ~/.config/max/cloudflared-bootstrap.yml
~/.local/bin/cloudflared tunnel login
~/.local/bin/cloudflared tunnel --config ~/.config/max/cloudflared-bootstrap.yml \
  create --credentials-file ~/.config/max/tunnel-credentials.json max-alexa
chmod 600 ~/.config/max/tunnel-credentials.json
```

Si ya existe el túnel de esta instalación, reutiliza su UUID y archivo privado.
No crees otro en cada despliegue. El certificado de administración de Cloudflare
se usa para provisionar; el servicio utiliza solo las credenciales de ese túnel.

Copia `deploy/cloudflared.example.yml` a `~/.config/max/cloudflared.yml` y
reemplaza UUID, ruta absoluta de credenciales y hostname. La última regla 404
debe permanecer. Asigna permisos 0600 al archivo. No uses el puerto administrativo
8787 como destino: el túnel debe llegar a la entrada restringida 8788.

```bash
~/.local/bin/cloudflared tunnel --config ~/.config/max/cloudflared.yml ingress validate
~/.local/bin/cloudflared tunnel --config ~/.config/max/cloudflared-bootstrap.yml \
  route dns UUID_DEL_TUNEL max.example.com
```

El comando DNS no debe sobrescribir registros existentes. Si la cuenta no tiene
permiso DNS, usa el panel del dominio para añadir un CNAME `max` cuyo destino
sea `UUID_DEL_TUNEL.cfargotunnel.com`, con proxy activado y TTL automático.
El dominio y túnel deben pertenecer a la cuenta adecuada. No hace falta abrir
puertos del router ni cambiar los registros de otros servicios.

## Servicios persistentes

Después de instalar MAX con `deploy/install.py`, instala sus tres unidades:

```bash
install -d ~/.config/systemd/user
install -m 644 deploy/max.service deploy/max-edge.service deploy/max-tunnel.service \
  ~/.config/systemd/user/
systemctl --user daemon-reload
systemd-analyze --user verify ~/.config/systemd/user/max.service \
  ~/.config/systemd/user/max-edge.service ~/.config/systemd/user/max-tunnel.service
systemctl --user enable --now openclaw-gateway.service max.service max-edge.service max-tunnel.service
```

La unidad del gateway presupone la instalación funcional de OpenClaw descrita
en [operación](OPERACION.md). Los servicios MAX se recuperan automáticamente
cuando su proceso termina, sin agotar un límite de intentos durante el arranque.
El túnel puede esperar a la red sin cambiar su identidad ni hostname.
`max.service` espera hasta tres minutos a que `/startupz` de OpenClaw confirme
`started`; el estado de proceso activo por sí solo no basta. Si aún no está
listo, systemd vuelve a intentar el arranque. Esto evita aceptar una primera
consulta mientras Codex todavía se inicializa. El gateway usa loopback 18789
por defecto; para otra instalación ajusta `--gateway-url` en `ExecStartPre`.
La espera no depende del estado de Telegram, WhatsApp u otros canales personales.

Habilita una vez la permanencia del gestor de usuario y el arranque de Docker
con una cuenta administradora:

```bash
sudo loginctl enable-linger "$USER"
sudo systemctl enable --now docker
loginctl show-user "$USER" -p Linger
```

El resultado debe incluir `Linger=yes`. Esto permite iniciar los servicios sin
sesión gráfica ni SSH. Home Assistant y SearXNG deben tener una política Docker
`unless-stopped` o `always`; `deploy/compose.yaml` ya configura la del buscador.
Un contenedor detenido manualmente con `unless-stopped` permanece detenido.

Guarda `public_url: "https://max.example.com"` en el JSON privado de MAX. Es un
campo informativo para `max-cli status`; no cambia DNS ni configura TLS.
En la consola Alexa, configura el endpoint de desarrollo HTTPS como
`https://max.example.com/alexa`. Comprueba primero el certificado y el estado
público. No uses un hostname temporal `trycloudflare.com` en esta configuración.

## Verificación de reinicio

```bash
~/.local/share/max/venv/bin/max-cli backup
cat /proc/sys/kernel/random/boot_id
systemctl --user is-enabled max.service max-edge.service max-tunnel.service openclaw-gateway.service
curl --fail https://max.example.com/health
```

Reinicia Linux de forma ordenada. Comprueba después que el ID de arranque cambió,
que las unidades y contenedores arrancaron automáticamente, y que la misma URL
responde con un certificado válido. Reiniciar solo `max.service` o el túnel no
equivale a reiniciar la laptop.

```bash
cat /proc/sys/kernel/random/boot_id
systemctl --user is-active max.service max-edge.service max-tunnel.service openclaw-gateway.service
docker inspect --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}} {{.State.Status}}' \
  homeassistant max-searxng
curl --fail https://max.example.com/health
~/.local/share/max/venv/bin/max-cli status
~/.local/share/max/venv/bin/max-cli ask "Responde brevemente que MAX está disponible" --wait
```

Verifica también que `/v1/status` sea 404 desde Internet y que `/alexa` rechace
peticiones sin firma. El simulador oficial de Alexa permite comprobar el nuevo
endpoint con solicitudes firmadas. Los dispositivos físicos se agregan aparte.

Si el runtime falla, `/health` devuelve 503; un proceso del túnel activo por sí
solo no demuestra que MAX esté listo. Diagnóstico:

```bash
journalctl --user -u max.service -u max-edge.service -u max-tunnel.service -n 80 --no-pager
```

Documentación oficial: [túneles locales de Cloudflare](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/create-local-tunnel/),
[reglas de ingreso](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/configuration-file/)
y [permanencia de usuario en systemd](https://www.freedesktop.org/software/systemd/man/latest/loginctl.html).
