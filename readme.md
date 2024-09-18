# Prox-Manager
A companion tool designed to streamline and enhance the control of virtual machine (VM) configurations on a Proxmox server

## Overview 
Prox-Manager simplifies VM management by enabling configuration changes based on templates, removing the need to manually adjust each parameter. It also provides a Python class interface for interacting with the Proxmox REST API

## Key Features
+ **Template-Based Configuration**: Apply pre-defined templates to dynamically modify VM settings, saving time and reducing manual effort.
+ **Python API Wrapper**: Provides a Python class for easier interaction with the Proxmox REST API, translating API calls into Python methods.

## Use Case
+ **Multi-OS Users**: Perfect for users who work with multiple operating systems and need to easily switch between configurations, such as provisioning hardware resources on the fly. 
+ **High-Performance Workstation**: Transform a VM into a high-powered workstation with hardware passthrough and enhanced processing capabilities.
+ **Low-Power Mode**: Adjust a VM's configuration to run in a lightweight, resource-efficient mode, ideal for low-intensity tasks.

## Getting Started
Define a `config.json` file with the following format:

``` json
    "server_adr": "https://*:8006/",
    "api_endpoint": "api2/json/",
    "auth_api": "access/ticket",
    "username": "*",
    "password": "*",

    "vms" :{
        "passthrough-100": {
            "agent": "Nullable",
            "cpu": "*",
            "bios": "*",
            "meta": "*",
            "digest": "*",
            "sockets": "*",
            "cores": 16,
            "numa": "*",
            "vmgenid": "*",
            "net0": "*",
            "machine": "*",
            "ostype": "*",
            "scsihw": "*",
            "scsi0": "*",
            "memory": "61440",
            "smbios1": "*",
            "efidisk0": "*",
            "name": "*",
            "boot": "*",
            "usb0": "host=05ac:024f",
            "usb1": "host=046d:c52b",
            "hostpci0": "0000:01:00,pcie=1,x-vga=1",
            "tpmstate0": "Nullable"
        },
    }
```
Within the vms section, each dictionary key represents a configuration name, with the value being the template used to update an existing VM configuration

### Key/Value Pair Formatting for VM Configuration Templates:
Note the following key/value pairs formating for a vm configuration template:
+ `"key": "*"`
    + The key must exist in the new configuration, but the value can be whatever it was before.
+ `"key": "Nullable"`
    + This indicates the key is optional. If it was not present in the previous configuration, it will not be added.
+ Any key with a specific value will be added to the new configuration.
+ Any key not present in the template but included in the previous configuration will be removed.

### Terminal UI 
Currently, by running the library file lib/prox.py, you can access a command-line tool to interact with the Prox-Manager class.

> Note: Future versions will include web, mobile, and desktop GUIs.

Example output from running python3 prox.py (in the `lib` directory):
```
--------------------------------------------------------------------------------------
Configs: ['passthrough-100', 'passthrough-75', 'passthrough-50', 'headlless-50','headlless-25']
Status: ['reboot', 'reset', 'resume', 'shutdown', 'start', 'stop', 'suspend']

Nodes:
* MainframeIX(1)
        - RigIX(101): running, passthrough-50
        - CyberRigIX(103): running, headlless-25
        - WinRigIX(102): stopped, headlless-25

Change VM Status: stat, {nodeid}, {vmid}, {status}
Change VM Config: conf, {nodeid}, {vmid}, {configs}
Quit: q

> {input goes here}
```

## Authors 
cysoq (Noah Soqui)

## Version History 

+ 0.1
    + Initial Release: Supports TUI and config changes via a hand-crafted config.json.

## Future features
+ Dynamically generated templates.
+ Template-based updates for multiple VMs simultaneously.
+ Actions based on existing templates and VM statuses.
+ Web, Desktop, and Mobile apps.
+ Improved error handling.