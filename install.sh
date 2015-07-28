CDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
APP=/usr/share/applications/vpnwatch.desktop

text="[Desktop Entry]\n
Version=1.0\n
Type=Application\n
Exec=$CDIR/vpnwatch.sh\n
Name=vpnwatch\n
Icon=$CDIR/vpnwatch/VPN.png"

echo -e $text > $APP

