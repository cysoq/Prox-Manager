import httpx
import json 
import logging
import os

def print_sorted_dict(d):
    # Sort the dictionary by keys
    print("{")
    for key in sorted(d.keys()):
        print(f"\t{key}: {d[key]}")
    print("}")

logging.basicConfig(
    level=logging.CRITICAL,  # This captures all levels of logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)

class prox_manager():
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("prox_manager")
        self.config_dict = self.get_config()
        self.base_adr =  self.config_dict["server_adr"] + self.config_dict["api_endpoint"]
        self.csrf_token = None
        self.ticket = None
        

    def get_config(self):
        self.logger.info("Got config")
        config_file = open("../config.json")
        dict = json.loads(config_file.read())
        return dict
    
    def auth_ticket_req(self):
        adr = self.base_adr + self.config_dict["auth_api"]

        auth_data = {
            "username": self.config_dict["username"],
            "password": self.config_dict["password"],
        }
        
        r = httpx.post(adr, verify=False, data=auth_data)

        if r.status_code > 199 and r.status_code < 300:
            auth_dict = r.json() # See all info: print(json.dumps(auth_dict, indent=4))
            self.csrf_token = auth_dict["data"]["CSRFPreventionToken"]
            self.ticket = auth_dict["data"]["ticket"]
            return True
        
        return False
    
    def verify_auth(self):

        if self.ticket is not None and self.csrf_token is not None:
            return True
        
        self.auth_ticket_req()
        if self.ticket is None or self.csrf_token is None: 
            self.logger.error("Failed to authenticate for get_req")
            return False
        return True
    
    def get_req(self, adr):

        if self.verify_auth() is False:
            return False
            
        cookies = {
            "PVEAuthCookie": self.ticket
        }

        r = httpx.get(adr, verify=False, cookies=cookies)
        return r
    
    def post_req(self, adr, data):
        if self.verify_auth() is False:
            return False
            
        cookies = {
            "PVEAuthCookie": self.ticket
        }

        headers = {
            "CSRFPreventionToken": self.csrf_token
        }

        r = httpx.post(adr, verify=False, cookies=cookies, headers=headers, data=data)
        return r        
    
    def get_nodes(self):
        r = self.get_req(self.base_adr + "nodes")
        return r.json()["data"]

    def get_nodes_hardware(self, node):
        hardware = {}
        r_pci = self.get_req(self.base_adr + f"nodes/{node}/hardware/pci")
        hardware["pci"] = r_pci.json()["data"]
        r_usb = self.get_req(self.base_adr + f"nodes/{node}/hardware/usb")
        hardware["usb"] = r_usb.json()["data"]
        # print(json.dumps(hardware, indent=4))
        return hardware

    def get_nodes_vms(self, node):
        r = self.get_req(self.base_adr + f"nodes/{node}/qemu")
        # print(json.dumps(r.json()["data"], indent=4))~
        return r.json()["data"]
    
    def get_vm_config(self, node, vmid):
        url = self.base_adr + f"nodes/{node}/qemu/{str(vmid)}/config"
        r = self.get_req(url)
        return r.json()["data"]

    def check_rig_config_type(self, vm_config):
        vm_config_str = json.dumps(vm_config, indent=4)

        vms = self.config_dict["vms"]
        vm_type_str = "hybrid"
        for vm_type in vms:
            vm_type_str = vm_type
            for hardware in vms[vm_type]:
                if vms[vm_type][hardware] == "Nullable":
                    #Does not matter if exists or not
                    continue
                elif hardware in vm_config:
                    if vms[vm_type][hardware] != "*" and vms[vm_type][hardware] != vm_config[hardware]:
                        # the hardware value is not a token, and does not match
                        vm_type_str = "hybrid"
                        break
                else:
                    vm_type_str = "hybrid"
                    break

            if vm_type_str != "hybrid":
                return vm_type_str
            
        return vm_type_str
    
    def update_rig_config_type(self, node, vmid, new_type):
        cur_vm_config = self.get_vm_config(node, vmid)

        new_vm_config = {}

        new_type_dict = vms = self.config_dict["vms"][new_type]

        for hardware in new_type_dict:
            if new_type_dict[hardware] == "Nullable" and hardware in cur_vm_config:
                # if the value was in the config, and nullable, will keep it in there
                new_vm_config[hardware] = cur_vm_config[hardware]
            elif new_type_dict[hardware] == "Nullable" and hardware not in cur_vm_config:      
                # was not in it before and nullable, will not add it
                continue        
            elif new_type_dict[hardware] == "*" and hardware in cur_vm_config:
                # a token and is in there, will keep what it was before
                new_vm_config[hardware] = cur_vm_config[hardware]
            elif new_type_dict[hardware] != "*" and hardware in cur_vm_config:
                # Will update the value that was in there
                new_vm_config[hardware] = new_type_dict[hardware]
            elif hardware not in cur_vm_config:
                new_vm_config[hardware] = new_type_dict[hardware]
            else:
                continue

        if self.check_rig_config_type(new_vm_config) == new_type:
            return new_vm_config
        
        self.logger.error("update_rig_config_type failed")
        return False
    
    def update_vm_config(self, node, vmid, new_vm_config_dict):
        if "meta" in new_vm_config_dict:
            del new_vm_config_dict["meta"] # Have to remove meta for it to update
        config_url = self.base_adr + f"nodes/{node}/qemu/{vmid}/config"

        r = self.post_req(config_url, data=new_vm_config_dict)

        if r.status_code > 199 and r.status_code < 300:
            return True

        return False
    
    def change_vm_status(self, node, vmid, status):
        config_url = self.base_adr + f"nodes/{node}/qemu/{vmid}/status/{status}"
        r = self.post_req(config_url, data={})

        if r.status_code > 199 and r.status_code < 300:
            print(r.content)
            return True

        return False

def main():
    prox_client = prox_manager()
    prox_client.auth_ticket_req()
    print(int(os.get_terminal_size()[0])*"-")
    
    while True:
        config_str = f"Configs: {list(prox_client.config_dict["vms"].keys())}"
        print(config_str)
        status_list = ["reboot", "reset", "resume", "shutdown", "start", "stop", "suspend"]
        print(f"Status: {status_list}\n")
        
        print("Nodes:")
        nodeid_dict ={}
        node_num_itr = 1
        for node_dict in prox_client.get_nodes():
            nodeid_dict[str(node_num_itr)] = {
                "nodename" :node_dict["node"],
                "vms" : []
                }
            print(f"* {node_dict["node"]}({node_num_itr})")
            nodes_vms = prox_client.get_nodes_vms(node_dict["node"])
        
            for vm in nodes_vms:
                
                (nodeid_dict[str(node_num_itr)]["vms"]).append(str(vm["vmid"]))
                vmconfig = prox_client.get_vm_config("MainframeIX", vm["vmid"])
                rig_type = prox_client.check_rig_config_type(vmconfig)
                print(f"\t- {vm["name"]}({vm["vmid"]}): {vm["status"]}, {rig_type}")
            
            node_num_itr += 1

        print("\nChange VM Status: stat, {nodeid}, {vmid}, {status}")
        print("Change VM Config: conf, {nodeid}, {vmid}, {configs}")
        print("Quit: q\n")
        user_input = input("> ")
        if user_input.strip() == "q":
            print("Exiting")
            exit()
        elif len(user_input.split(",")) == 4:
            command_list =  user_input.split(",")

            # Change the status (option 1)
            if command_list[0].strip() == "stat":
                if (command_list[1].strip() in nodeid_dict.keys() 
                    and command_list[2].strip() in nodeid_dict[command_list[1].strip()]["vms"] 
                    and command_list[3].strip() in status_list):

                    node = nodeid_dict[command_list[1].strip()]["nodename"]
                    vmid = command_list[2].strip()
                    status = command_list[3].strip()

                    if prox_client.change_vm_status(node, vmid, status) is True:
                        print("Changing Status") 
                    else: 
                        print("Status Change failed") 

            # Change the config (option 2)
            elif command_list[0].strip() == "conf":
                if (command_list[1].strip() in nodeid_dict.keys() 
                    and command_list[2].strip() in nodeid_dict[command_list[1].strip()]["vms"] 
                    and command_list[3].strip() in prox_client.config_dict["vms"].keys()):

                    node = nodeid_dict[command_list[1].strip()]["nodename"]
                    vmid = command_list[2].strip()
                    new_config_type = command_list[3].strip()

                    new_config = prox_client.update_rig_config_type(node, vmid, new_config_type)
                
                    if prox_client.update_vm_config(node, vmid, new_config) is True:
                        print("Changing Config")
                    else:
                        print("Config Change failed") 
            else:
                print("Command Not Recognized")
        else:
            print("Command Not Recognized")

        print()
        print(int(os.get_terminal_size()[0])*"-")

# Main body
if __name__ == '__main__':
    main()