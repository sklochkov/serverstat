%define _builddir	.
%define _sourcedir	.
%define _specdir	.
%define _rpmdir		.

Name:		server resource usage monitor
Version:	0.1
Release:	1%{dist}

Summary:	CPU usage monitor
License:	MIT
Group:		System Environment/Libraries
Distribution:	Red Hat Enterprise Linux

BuildArch:	noarch

BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
%{?el5:Requires: python26}

%description
server resource usage monitor


%prep


%build


%install
%{__rm} -rf %{buildroot}
install -d -m755 %{buildroot}/etc/init.d
install -d -m755 %{buildroot}/usr/local/bin
install -m755 serverstat.py %{buildroot}/usr/local/bin/serverstat.py
install -m755 serverstat.init %{buildroot}/etc/init.d/serverstat

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ $1 -eq 1 ] ; then
	chkconfig --add serverstat
	chkconfig serverstat on
	/etc/init.d/serverstat start
elif [ $1 -eq 2 ] ; then
	/etc/init.d/serverstat restart
fi

%preun
if [ $1 -eq 0 ] ; then
	chkconfig serverstat off
	chkconfig --del serverstat
	/etc/init.d/serverstat stop
fi

%files
%defattr(-,root,root)
%attr(0755,root,root) /usr/local/bin/serverstat.py
%attr(0755,root,root) /etc/init.d/serverstat


