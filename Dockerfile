FROM quay.io/centos/centos:stream8

# Update the system and install necessary tools
RUN dnf -y update && \
    dnf -y install wget bzip2 unzip git mesa-dri-drivers

# Set up virtual display
#ENV DISPLAY=:99

# Start Xvfb
#CMD ["Xvfb", ":99", "-ac"]

# Install the newest version of KLayout
RUN wget https://www.klayout.org/downloads/CentOS_8/klayout-0.28.12-0.x86_64.rpm -O ~/klayout.rpm && \
    dnf -y localinstall ~/klayout.rpm && \
    rm ~/klayout.rpm

# Clone SiEPIC-Tools and SiEPIC_EBeam_PDK 
RUN mkdir -p /root/.klayout/salt && \
    cd /root/.klayout/salt && \
    git clone --branch v0.4.5 https://github.com/SiEPIC/SiEPIC-Tools.git && \
    git clone https://github.com/SiEPIC/SiEPIC_EBeam_PDK.git

# Set the working directory
WORKDIR /home

# Set PATH
ENV PATH="/usr/local/bin:${PATH}"
ENV QT_QPA_PLATFORM=minimal
