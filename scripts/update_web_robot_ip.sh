#!/usr/bin/env bash
set -euo pipefail

ROOT="."
ROBOT_IP=""
NO_BACKUP=0

usage() {
  cat <<'EOF'
Uso:
  ./scripts/update_web_robot_ip.sh [-p RUTA_WEB] [-i IP] [--no-backup]

Opciones:
  -p, --path       Carpeta donde buscar el codigo de la web. Por defecto: .
  -i, --ip         IP del PC/robot que ejecuta ROS. Si no se indica, se intenta detectar.
  --no-backup      No crear copias .bak de los archivos modificados.
  -h, --help       Mostrar esta ayuda.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--path)
      ROOT="${2:-}"
      shift 2
      ;;
    -i|--ip)
      ROBOT_IP="${2:-}"
      shift 2
      ;;
    --no-backup)
      NO_BACKUP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opcion no reconocida: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "La ruta no existe o no es una carpeta: $ROOT"
  exit 1
fi

detect_ips() {
  if command -v ip >/dev/null 2>&1; then
    ip -4 -o addr show scope global up |
      awk '{print $4}' |
      cut -d/ -f1 |
      grep -Ev '^(127\.|169\.254\.)' |
      sort -u
  elif command -v hostname >/dev/null 2>&1; then
    hostname -I 2>/dev/null |
      tr ' ' '\n' |
      grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' |
      grep -Ev '^(127\.|169\.254\.)' |
      sort -u
  fi
}

if [[ -z "$ROBOT_IP" ]]; then
  mapfile -t LOCAL_IPS < <(detect_ips || true)

  if [[ "${#LOCAL_IPS[@]}" -eq 1 ]]; then
    DETECTED_IP="${LOCAL_IPS[0]}"
    read -r -p "IP detectada: $DETECTED_IP. Pulsa Enter para usarla o escribe otra IP: " ANSWER
    ROBOT_IP="${ANSWER:-$DETECTED_IP}"
  elif [[ "${#LOCAL_IPS[@]}" -gt 1 ]]; then
    echo "Se han detectado varias IPs:"
    for i in "${!LOCAL_IPS[@]}"; do
      printf " %d. %s\n" "$((i + 1))" "${LOCAL_IPS[$i]}"
    done

    read -r -p "Elige un numero, pulsa Enter para usar la primera, o escribe otra IP: " ANSWER
    if [[ -z "$ANSWER" ]]; then
      ROBOT_IP="${LOCAL_IPS[0]}"
    elif [[ "$ANSWER" =~ ^[0-9]+$ ]] && (( ANSWER >= 1 && ANSWER <= ${#LOCAL_IPS[@]} )); then
      ROBOT_IP="${LOCAL_IPS[$((ANSWER - 1))]}"
    else
      ROBOT_IP="$ANSWER"
    fi
  else
    read -r -p "No se pudo detectar la IP. Introduce la IP del PC/robot que ejecuta ROS: " ROBOT_IP
  fi
fi

ROBOT_IP="$(printf '%s' "$ROBOT_IP" | xargs)"

if [[ -z "$ROBOT_IP" ]]; then
  echo "No se ha introducido ninguna IP. Cancelado."
  exit 1
fi

mapfile -d '' FILES < <(
  find "$ROOT" \
    \( -path '*/.git/*' -o -path '*/node_modules/*' -o -path '*/dist/*' -o -path '*/build/*' -o -path '*/.next/*' -o -path '*/out/*' -o -path '*/coverage/*' \) -prune \
    -o -type f \
    \( -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.html' -o -name '*.css' -o -name '*.json' -o -name '*.md' -o -name '.env*' \) \
    ! -name '*.bak' \
    -print0
)

CHANGED=()

for FILE in "${FILES[@]}"; do
  if grep -Eq 'localhost:9090|127\.0\.0\.1:9090|localhost:8081|127\.0\.0\.1:8081|IP_DEL_ROBOT_O_PC_ROS|IP_DEL_PC' "$FILE"; then
    if [[ "$NO_BACKUP" -eq 0 ]]; then
      cp "$FILE" "$FILE.bak"
    fi

    perl -0pi -e "s/(localhost|127\\.0\\.0\\.1)(:9090)/$ROBOT_IP\$2/g; s/(localhost|127\\.0\\.0\\.1)(:8081)/$ROBOT_IP\$2/g; s/IP_DEL_ROBOT_O_PC_ROS/$ROBOT_IP/g; s/IP_DEL_PC/$ROBOT_IP/g" "$FILE"
    CHANGED+=("$FILE")
  fi
done

if [[ "${#CHANGED[@]}" -eq 0 ]]; then
  echo "No se encontraron URLs localhost/127.0.0.1 ni placeholders para cambiar en: $ROOT"
  exit 0
fi

echo
echo "Archivos actualizados con la IP $ROBOT_IP:"
printf ' - %s\n' "${CHANGED[@]}"

if [[ "$NO_BACKUP" -eq 0 ]]; then
  echo
  echo "Se han creado copias .bak junto a cada archivo modificado."
fi

echo
echo "Recuerda probar estos endpoints desde el navegador:"
echo " - ws://$ROBOT_IP:9090"
echo " - http://$ROBOT_IP:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg"
