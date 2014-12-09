Name:		makerbot_driver
Version:	2.0.0
Release:	1%{?dist}
Summary:	Python driver for communicating with MakerBot 3D printers

License:	AGPL
URL:		http://github.com/makerbot/s3g
Source:		%{name}-%{version}.tar.gz

BuildRequires:	python >= 2.7, python-setuptools, python-mock, python-lockfile, python-unittest2, mb_pyserial = 2.0.0
Requires:	python >= 2.7, python-setuptools, python-mock, python-lockfile, python-unittest2, mb_pyserial = 2.0.0

%description
This library permits a python2.7 script to discover and control a 
Replicator or other 3d printing device that supports the s3g
protocol.


%prep
%setup -q -n s3g


%build
mkdir -p %{buildroot}/%{_datarootdir}/makerbot
cp -r %{_datarootdir}/makerbot/python %{buildroot}/%{_datarootdir}/makerbot/
scons install_prefix=%{buildroot}/%{_prefix} config_prefix=%{buildroot}/%{_sysconfdir}


%install
rm -rf %{buildroot}
scons install_prefix=%{buildroot}/%{_prefix} config_prefix=%{buildroot}/%{_sysconfdir} install


%files
%{_datarootdir}/makerbot/python/makerbot_driver-*.egg
%{_datarootdir}/makerbot/s3g/


%changelog
