#!/bin/sh

	echo "============================================================="
	echo "           Uninstall Script for VYZEX MPK88-61               "
	echo "-------------------------------------------------------------"
	echo " ALL PROGRAM & CONFIG FILES WILL BE DELETED !!!              "
	echo " YOUR .SQS FILES WILL BE LEFT INTACT.                        "
	echo " /Library/Application Support/Psicraft/Vyzex MPK88-61/ "
#	echo " ~/Library/Preferences/Psicraft/Vyzex Floor MPK88-61/        "
	echo "-------------------------------------------------------------"

sudo -k

if sudo -l -p " Please enter root password: " ; then
	echo "--------------------------------------------------"

	echo " ----- Removing Receipts..."
	sudo rm -rf /Library/Receipts/Vyzex\ MPK88-61*.pkg

	echo " ----- Removing Applications..."
	sudo rm -rf /Applications/Vyzex\ MPK88-61*.app

	echo " ----- Removing Application Files..."
	sudo rm -rf /Library/Application\ Support/Psicraft/Vyzex\ MPK88-61/

	echo " ----- Removing User Settings..."
        sudo rm -rf ~/Library/Preferences/Psicraft/Vyzex\ MPK88-61/*.*
        sudo rm -rf ~/Library/Preferences/Psicraft/Vyzex\ MPK88-61/.DS_Store
	sudo rmdir ~/Library/Preferences/Psicraft/Vyzex\ MPK88-61

	echo " ----- Removing Property Lists..."
	sudo rm -rf /Library/Preferences/com.psicraft.vyzex.mpk88-61*.plist
	sudo rm -rf ~/Library/Preferences/com.psicraft.vyzex.mpk88-61*.plist


	echo "--------------------------------------------------"
	echo " Uninstall Completed."
	echo "=================================================="

	sudo -k

else
	echo " Uninstall Cancelled."
	echo "=================================================="

fi