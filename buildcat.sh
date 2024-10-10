#!/bin/bash

UBUNTU_VERSION=$(lsb_release -rs)

check_os_version() {
    if [[ "$UBUNTU_VERSION" != "22.04" && "$UBUNTU_VERSION" != "20.04" ]]; then
        echo "Error: Unsupported Ubuntu version: $UBUNTU_VERSION. This script only works on Ubuntu 20.04 or 22.04."
        exit 1
    fi
    echo "Ubuntu version $UBUNTU_VERSION detected. Proceeding with the script..."
}

keep_sudo_alive() {
    while true; do
        sudo -n true
        sleep 60
        kill -0 "$$" || exit
    done 2>/dev/null &
}

install_dependencies() {
    echo "Installing dependencies..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y build-essential libtool autotools-dev automake pkg-config bsdmainutils curl git cmake
    
    if [[ "$TARGET" == "Windows" ]]; then
        echo "Installing packaging libraries for cross-compiling to Windows..."
        sudo apt install -y nsis
        
        if [[ "$UBUNTU_VERSION" == "22.04" ]]; then
            sudo apt install -y g++-mingw-w64-x86-64-posix
        elif [[ "$UBUNTU_VERSION" == "20.04" ]]; then
            sudo apt install -y g++-mingw-w64-x86-64
            sudo update-alternatives --config x86_64-w64-mingw32-g++
        fi
    fi
}

clone_repository() {
    echo "Cloning the Catcoin repository..."
    git clone https://github.com/ahmedbodi/catcoin-new.git
    cd catcoin-new
    echo "Checking out v2.0.0-beta15..."
    git checkout v2.0.0-beta15
}

build_dependencies() {
    echo "Building dependency libraries..."
    PATH=$(echo "$PATH" | sed -e 's/:\/mnt.*//g')
    
    if grep -q microsoft /proc/version; then
        echo "Disabling WSL support for Win32 applications..."
        sudo bash -c "echo 0 > /proc/sys/fs/binfmt_misc/status"
    fi
    
    cd depends
    compile_fix
    cd ..
}

compile_fix() {
    FILE_TO_MODIFY="/home/$(whoami)/source/catcoin-new/depends/work/build/x86_64-*/qt/5.9.8-*/qtbase/src/corelib/tools/qbytearraymatcher.h"
    INCLUDE_STATEMENT="#include <limits>"
    MAKE_COMMAND="make $(grep -q microsoft /proc/version && echo 'HOST=x86_64-w64-mingw32')"
    ERROR_LOG="error.log"

    $MAKE_COMMAND 2> $ERROR_LOG

    if grep -q "qbytearraymatcher.h" $ERROR_LOG; then
        echo "Error detected in qbytearraymatcher.h during the compilation process."
        if ! grep -q "$INCLUDE_STATEMENT" $FILE_TO_MODIFY; then
            echo "Adding #include <limits> to $FILE_TO_MODIFY"
            sudo sed -i '1i#include <limits>' $FILE_TO_MODIFY
        else
            echo "#include <limits> already present in $FILE_TO_MODIFY"
        fi
        echo "Rerunning make command after applying the compile fix..."
        $MAKE_COMMAND
        [ $? -eq 0 ] && echo "Compilation completed successfully." || echo "Compilation failed after modifying the file."
    else
        echo "No errors related to qbytearraymatcher.h detected. Compilation successful."
    fi

    rm -f $ERROR_LOG
}

run_autogen_and_configure() {
    echo "Running autogen.sh for $TARGET compilation..."
    ./autogen.sh
    if [[ "$TARGET" == "Windows" ]]; then
        CONFIG_SITE=$PWD/depends/x86_64-w64-mingw32/share/config.site ./configure --prefix=/
    else
        CONFIG_SITE=$PWD/depends/x86_64-pc-linux-gnu/share/config.site ./configure --prefix=/
    fi
}

compile_catcoin() {
    echo "Compiling Catcoin..."
    make -j$(nproc)
    
    if grep -q microsoft /proc/version; then
        echo "Enabling WSL support for Win32 applications again..."
        sudo bash -c "echo 1 > /proc/sys/fs/binfmt_misc/status"
    fi
}

install_or_package_catcoin() {
    if [[ "$TARGET" == "Windows" ]]; then
        echo "Installing Catcoin for Windows to $HOME/catcoin-windows..."
        sudo make install DESTDIR=$HOME/catcoin-windows
        echo "Creating Windows installer package..."
        sudo make deploy
    else
        echo "Installing Catcoin for Ubuntu to $HOME/catcoin-linux..."
        sudo make install DESTDIR=$HOME/catcoin-linux
    fi
}

main() {
    echo "Starting the build process for Catcoin..."
    check_os_version
    sudo -v
    keep_sudo_alive

    TARGET=$(grep -q microsoft /proc/version && echo "Windows" || echo "Ubuntu")
    echo "Target platform is $TARGET $([ "$TARGET" == "Windows" ] && echo "(cross-compilation)")"

    install_dependencies
    clone_repository
    build_dependencies
    run_autogen_and_configure
    compile_catcoin
    install_or_package_catcoin

    echo "Catcoin build process completed for $TARGET!"
}

main
