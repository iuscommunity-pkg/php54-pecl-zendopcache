%{!?php_inidir: %{expand: %%global php_inidir %{_sysconfdir}/php.d}}
%{!?__php:      %{expand: %%global __php      %{_bindir}/php}}
%{!?__pecl:     %{expand: %%global __pecl     %{_bindir}/pecl}}
%global with_zts   0%{?__ztsphp:1}
%global proj_name  ZendOpcache
%global pecl_name  zendopcache
%global plug_name  opcache

%define real_name php-pecl-zendopcache
%define php_base php54

Name:          %{php_base}-pecl-%{pecl_name}
Version:       7.0.5
Release:       1%{?dist}
Summary:       The Zend OPcache

Group:         Development/Libraries
License:       PHP
URL:           http://pecl.php.net/package/%{proj_name}
Source0:       http://pecl.php.net/get/%{pecl_name}-%{version}.tgz
# this extension must be loaded before XDebug
# So "opcache" if before "xdebug"
Source1:       %{plug_name}.ini
Source2:       %{plug_name}-default.blacklist

# Credit to Remi for the following Sources from
# http://dl.fedoraproject.org/pub/epel/6/SRPMS/php-pecl-zendopcache-7.0.3-1.el6.src.rpm
Source3:       https://raw2.github.com/zendtech/ZendOptimizerPlus/e8e28cd95c8aa660c28c2166da679b50deb50faa/tests/blacklist.inc
Source4:       https://raw2.github.com/zendtech/ZendOptimizerPlus/e8e28cd95c8aa660c28c2166da679b50deb50faa/tests/php_cli_server.inc

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: %{php_base}-devel >= 5.4.0
BuildRequires: %{php_base}-pear

Requires(post): %{__pecl}
Requires(postun): %{__pecl}
Requires:      %{php_base}(zend-abi) = %{php_zend_api}
Requires:      %{php_base}(api) = %{php_core_api}

# Only one opcode cache could be enabled
Conflicts:     %{php_base}-mmcache %{php_base}-eaccelerator
Conflicts:     %{php_base}-xcache
# APC 3.1.15 offer an option to disable opcache
Conflicts:     %{php_base}-pecl-apc < 3.1.15
Provides:      php-pecl(%{plug_name}) = %{version}%{?prever}
Provides:      %{php_base}-pecl(%{plug_name}) = %{version}%{?prever}
Provides:      php-pecl(%{plug_name})%{?_isa} = %{version}%{?prever}
Provides:      %{php_base}-pecl(%{plug_name})%{?_isa} = %{version}%{?prever}
Provides:      php-%{plug_name} = %{version}-%{release}
Provides:      %{php_base}-%{plug_name} = %{version}-%{release}
Provides:      php-%{plug_name}%{?_isa} = %{version}-%{release}
Provides:      %{php_base}-%{plug_name}%{?_isa} = %{version}-%{release}

# Filter private shared
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}


%description
The Zend OPcache provides faster PHP execution through opcode caching and
optimization. It improves PHP performance by storing precompiled script
bytecode in the shared memory. This eliminates the stages of reading code from
the disk and compiling it on future access. In addition, it applies a few
bytecode optimization patterns that make code execution faster.


%prep
%setup -q -c
mv %{pecl_name}-%{version} NTS

cp %{SOURCE3} %{SOURCE4} NTS/tests/
cd NTS

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_ZENDOPCACHE_VERSION/{s/.*\s"//;s/".*$//;p}' ZendAccelerator.h)
echo ${extver}
if test "x${extver}" != "x%{version}%{?prever:-%{prever}}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}%{?prever:-%{prever}}.
   exit 1
fi
cd ..

%if %{with_zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif


%build
cd NTS
%{_bindir}/phpize
%configure \
    --enable-optimizer-plus \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
%configure \
    --enable-optimizer-plus \
    --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
install -D -p -m 644 %{SOURCE1} %{buildroot}%{php_inidir}/%{plug_name}.ini
sed -e 's:@EXTPATH@:%{php_extdir}:' \
    -i %{buildroot}%{php_inidir}/%{plug_name}.ini

make -C NTS install INSTALL_ROOT=%{buildroot}

%if %{with_zts}
install -D -p -m 644 %{SOURCE1} %{buildroot}%{php_ztsinidir}/%{plug_name}.ini
sed -e 's:@EXTPATH@:%{php_ztsextdir}:' \
    -i %{buildroot}%{php_ztsinidir}/%{plug_name}.ini

make -C ZTS install INSTALL_ROOT=%{buildroot}
%endif

# The default Zend OPcache blacklist file
install -D -p -m 644 %{SOURCE2} %{buildroot}%{php_inidir}/%{plug_name}-default.blacklist

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml


%check
cd NTS
%{__php} \
    -n -d zend_extension=%{buildroot}%{php_extdir}/%{plug_name}.so \
    -m | grep "Zend OPcache"

TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n -d zend_extension=%{buildroot}%{php_extdir}/%{plug_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php

%if %{with_zts}
cd ../ZTS
%{__ztsphp} \
    -n -d zend_extension=%{buildroot}%{php_ztsextdir}/%{plug_name}.so \
    -m | grep "Zend OPcache"

TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n -d zend_extension=%{buildroot}%{php_ztsextdir}/%{plug_name}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php
%endif


%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%files
%doc NTS/{LICENSE,README}
%config(noreplace) %{php_inidir}/%{plug_name}-default.blacklist
%config(noreplace) %{php_inidir}/%{plug_name}.ini
%{php_extdir}/%{plug_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{plug_name}.ini
%{php_ztsextdir}/%{plug_name}.so
%endif

%{pecl_xmldir}/%{name}.xml


%changelog
* Tue Apr 14 2015 Ben Harper <ben.harper@rackspace.com> - 7.0.5-1.ius
- Latest upstream
- remove patch1, fixed upstream
- update sed for PHP_ZENDOPCACHE_VERSION to reflect upstream changes

* Mon Jan 12 2015 Carl George <carl.george@rackspace.com> - 7.0.4-1.ius
- Latest upstream
- Add patch1 to clean up false positive in test suite

* Mon Aug 04 2014 Ben Harper <ben.harper@rackspace.com> - 7.0.3-1.ius
- latest release,  7.0.3
- disable Patch0, patched upstream
- add Source3 and Source4

* Thu Jun 06 2013 Ben Harper <ben.harper@rackspace.com> - 7.0.1-4.ius
- update BuildRequires, Requires and Provides

* Tue May 14 2013 Ben Harper <ben.harper@rackspace.com> - 7.0.1-3.ius
- porting from EPEL

* Thu Apr 11 2013 Remi Collet <rcollet@redhat.com> - 7.0.1-2
- allow wildcard in opcache.blacklist_filename and provide
  default /etc/php.d/opcache-default.blacklist

* Mon Mar 25 2013 Remi Collet <remi@fedoraproject.org> - 7.0.1-1
- official PECL release, version 7.0.1 (beta)
- rename to php-pecl-zendopcache

* Mon Mar 18 2013 Remi Collet <remi@fedoraproject.org> - 7.0.1-0.1.gitcef6093
- update to git snapshot, with new name (opcache)

* Sun Mar 10 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-2
- allow to install with APC >= 3.1.15 (user data cache)

* Tue Mar  5 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-1
- official PECL release, version 7.0.0 (beta)

* Thu Feb 28 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.7.gitd39a49a
- new snapshot
- run test suite during build

* Thu Feb 21 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.6.git3a06991
- new snapshot

* Fri Feb 15 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.4.git2b6eede
- new snapshot (ZTS fixes)

* Thu Feb 14 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.3.gita84b588
- make zts build optional

* Thu Feb 14 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.2.gitafb43f5
- new snapshot
- better default configuration file (new upstream recommendation)
- License file now provided by upstream

* Wed Feb 13 2013 Remi Collet <remi@fedoraproject.org> - 7.0.0-0.1.gitaafc145
- initial package
