# put into separate file for better reading experience
locals {
  metadata_startup_script = <<EOF
echo "Installing Ops Agent..." >> /startup-script.log
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Function to find the network adapter name by IP address
get_adapter_by_ip() {
    local ip_address="$1"
    local interface_name

    # Use `ip` command to show link information and grep for the IP address
    interface_name=$(ip -4 addr show | grep -w "$ip_address" | awk '{print $NF}')

    # Check if an interface name was found
    if [ -n "$interface_name" ]; then
        echo "$interface_name"
    else
        echo "No interface found for IP address: $ip_address"
    fi
}

echo "Getting adapters by IP..." >> /startup-script.log
source_eth=$(get_adapter_by_ip "${var.nat_router_source.interface_ip}")
echo "Source adapter: $source_eth (${var.nat_router_source.interface_ip})" >> /startup-script.log
dest_eth=$(get_adapter_by_ip "${var.nat_router_destination.interface_ip}")
echo "Destination adapter: adapter $dest_eth (${var.nat_router_destination.interface_ip}) " >> /startup-script.log

echo "Enable IP forwarding..." >> /startup-script.log
sudo echo -e "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sudo sysctl -w net.ipv4.ip_forward=1

echo "Setup NAT routing..." >> /startup-script.log
sudo iptables --flush
sudo iptables -t nat -A POSTROUTING -o $dest_eth -j MASQUERADE
sudo iptables -A FORWARD -i $source_eth -o $dest_eth -j ACCEPT
sudo iptables -A FORWARD -i $dest_eth -o $source_eth -m state --state ESTABLISHED,RELATED -j ACCEPT

echo "Add ${length(var.preroutings)} prerouting(s)..." >> /startup-script.log
%{for prerouting in var.preroutings}
sudo iptables -t nat -A PREROUTING -i $source_eth -p tcp -m tcp --dport ${prerouting.source_port} -j DNAT --to-destination ${prerouting.destination_ip}:${prerouting.destination_port}
%{endfor}

echo "Add ${length(var.routes)} route(s)..." >> /startup-script.log
%{for route in var.routes}
sudo ip route add "${route.destination_ip_range}" via "${route.via_ip}" dev $dest_eth
%{endfor}

echo "Printing results..." >> /startup-script.log
sudo echo "======== start of ip route show ========" >> /startup-script.log
sudo ip route show >> /startup-script.log
sudo echo "======== end of ip route show ========" >> /startup-script.log

sudo echo "======== start of iptables --list ========" >> /startup-script.log
sudo iptables --list >> /startup-script.log
sudo echo "======== end of iptables --list ========" >> /startup-script.log
echo "Setup complete." >> /startup-script.log
EOF
}
