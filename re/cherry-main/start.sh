#!/bin/bash

RED='\033[0;31m'
NC='\033[0m' 

echo -e "${RED}Installing dependencies...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install requests colorama
python3 -m pip install requests requests

echo -e "${RED}Starting main.py...${NC}"
python3 main.py

echo -e "${RED}Press Enter to exit...${NC}"
read
