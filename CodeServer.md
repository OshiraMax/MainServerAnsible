# Структура проекта


MainServer
├── CodeServer.md
├── main.yml
├── roles
│   ├── certbot
│   │   ├── tasks
│   │   │   ├── main.yml
│   ├── docker
│   │   ├── handlers
│   │   │   ├── main.yml
│   │   ├── tasks
│   │   │   ├── main.yml
│   │   ├── templates
│   │   │   ├── daemon.json.j2
│   │   ├── vars
│   │   │   ├── main.yml
│   ├── fail2ban
│   │   ├── handler
│   │   │   ├── task.yml
│   │   ├── tasks
│   │   │   ├── main.yml
│   ├── mongodb
│   │   ├── notify
│   │   │   ├── main.yml
│   │   ├── tasks
│   │   │   ├── main.yml
│   │   ├── vars
│   │   │   ├── main.yml
│   ├── nginx
│   │   ├── tasks
│   │   │   ├── main.yml
│   ├── postgresql
│   │   ├── handlers
│   │   │   ├── main.yml
│   │   ├── tasks
│   │   │   ├── main.yml
│   │   ├── vars
│   │   │   ├── main.yml
│   ├── prometheus
│   │   ├── tasks
│   │   │   ├── main.yml
│   │   ├── templates
│   │   │   ├── prometheus.yml.j2
│   │   ├── vars
│   │   │   ├── main.yml
│   ├── ufw
│   │   ├── handler
│   │   ├── tasks
│   │   │   ├── main.yml


# Код проекта

- **CodeServer.md**



- **main.yml**

---
- hosts: my_servers
  become: yes

  pre_tasks:
    - name: Обновление списка пакетов
      apt:
        update_cache: yes

  collections:
    - community.postgresql
    - community.mongodb

  vars:
    ansible_python_interpreter: /usr/bin/python3.12

  roles:
    - ufw
    - fail2ban
    - nginx
    - docker
    - certbot
    - postgresql 
    - mongodb
    - prometheus
    


## roles

### certbot

#### tasks

- **main.yml**

---
- name: Установка Certbot и его зависимостей
  apt:
    name:
      - certbot
      - python3-certbot-nginx
    state: present


### docker

#### handlers

- **main.yml**

---
- name: Перезапустить Docker
  systemd:
    name: docker
    state: restarted
    enabled: true
  listen: Перезапустить Docker

#### tasks

- **main.yml**

---
- name: Установка зависимостей для Docker
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - software-properties-common
    state: present

- name: Добавление официального Docker GPG ключа
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Добавление Docker репозитория
  apt_repository:
    repo: deb https://download.docker.com/linux/ubuntu focal stable
    state: present
    update_cache: yes

- name: Установка Docker CE
  apt:
    name: docker-ce
    state: present

- name: Проверить наличие директории для Docker данных на внешнем диске
  stat:
    path: "{{ docker_data_root }}"
  register: docker_data_dir

- name: Создать директорию для Docker данных на внешнем диске, если её нет
  file:
    path: "{{ docker_data_root }}"
    state: directory
    owner: root
    group: root
    mode: '0755'
  when: docker_data_dir.stat.exists is not defined or not docker_data_dir.stat.exists

- name: Проверить наличие файла конфигурации Docker
  stat:
    path: /etc/docker/daemon.json
  register: docker_daemon_config

- name: Убедиться, что конфигурация Docker установлена
  template:
    src: daemon.json.j2
    dest: /etc/docker/daemon.json
    mode: '0644'
    owner: root
    group: root
  notify: Перезапустить Docker
  when: docker_daemon_config.stat.exists == false or docker_daemon_config.stat.checksum != lookup("file", "templates/daemon.json.j2") | checksum




#### templates

- **daemon.json.j2**

{
  "data-root": "{{ docker_data_root }}"
}


#### vars

- **main.yml**

docker_data_root: "/mnt/server_drive/Servers"

### fail2ban

#### handler

- **task.yml**

---
- name: Перезапустить или запустить fail2ban, если не запущен
  service:
    name: fail2ban
    state: started
    enabled: true


#### tasks

- **main.yml**

---
- name: Проверить, установлен ли fail2ban
  apt:
    name: fail2ban
    state: present
  register: fail2ban_installed

- debug:
    msg: "Fail2Ban установлен"

- name: Проверить наличие файла /etc/fail2ban/jail.local
  stat:
    path: /etc/fail2ban/jail.local
  register: jail_local_file

- name: Скопировать конфигурацию fail2ban, если jail.local не существует
  command: cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
  when: jail_local_file.stat.exists == False
  notify: Перезапустить fail2ban





### mongodb

#### notify

- **main.yml**

- name: Перезапустить MongoDB
  service:
    name: mongod
    state: restarted


#### tasks

- **main.yml**

---
- name: Добавление репозитория focal-security для libssl1.1
  apt_repository:
    repo: "deb http://security.ubuntu.com/ubuntu focal-security main"
    state: present
    update_cache: yes

- name: Установка пакета libssl1.1
  apt:
    name: libssl1.1
    state: present

- name: Добавление ключа GPG для MongoDB
  ansible.builtin.shell: "curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-org-archive-keyring.gpg"
  args:
    creates: /usr/share/keyrings/mongodb-org-archive-keyring.gpg

- name: Добавление репозитория MongoDB
  apt_repository:
    repo: "deb [signed-by=/usr/share/keyrings/mongodb-org-archive-keyring.gpg] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse"
    state: present
    update_cache: yes

- name: Установка MongoDB
  apt:
    name: mongodb-org
    state: present

- name: Создать каталог данных для MongoDB на внешнем диске
  file:
    path: "/mnt/server_drive/Database/mongodb"
    state: directory
    owner: mongodb
    group: mongodb
    mode: '0755'
  become: yes

- name: Обновить конфигурацию MongoDB для использования нового каталога данных
  lineinfile:
    path: /etc/mongod.conf
    regexp: '^  dbPath:'
    line: "  dbPath: /mnt/server_drive/Database/mongodb"
  notify: Перезапустить MongoDB
  become: yes

- name: Убедиться, что MongoDB запущен и включен
  systemd:
    name: mongod
    state: started
    enabled: true

- name: Установка библиотеки pymongo
  apt:
    name: python3-pymongo
    state: present
  become: yes

- name: Создание пользователя базы данных
  community.mongodb.mongodb_user:
    name: "{{ mongodb_user }}"
    password: "{{ mongodb_password }}"
    database: "{{ mongodb_database }}"
    roles:
      - readWrite
      - dbAdmin
    state: present
    update_password: on_create


#### vars

- **main.yml**

$ANSIBLE_VAULT;1.1;AES256
65626634353865663235316630356335356465356634303663333664653661376434356663363837
3364313531636130316135626363363739303462643866390a616564623734633061316266663835
32373635626532343562306263366665643835333966633236643931353766303266303238386361
6637303131303533330a316633343337623466343636343238623638373265633166363337316334
30666362653862323531616566663531643263393963663262303636613733306561336566356164
32303732663163666331343338316663313435313066366436663031653763633666353061343132
38653166376463313061393930616139323964626235373061633565346566623662323732303239
66346266653733396333663331663761663237313938663864323962626139326434643336626533
3838


### nginx

#### tasks

- **main.yml**

---
- name: Проверить, установлен ли nginx
  apt:
    name: nginx
    state: present
  register: nginx_installed

- debug:
    msg: "Nginx установлен"

- name: Проверить, что NGINX запущен
  service:
    name: nginx
    state: started



### postgresql

#### handlers

- **main.yml**

---
- name: Перезапустить PostgreSQL
  service:
    name: postgresql
    state: restarted


#### tasks

- **main.yml**

---
- name: Установка пакета acl для поддержки ACL
  apt:
    name: acl
    state: present

- name: Установка зависимостей для работы с PostgreSQL в Ansible
  apt:
    name:
      - python3-psycopg2
    state: present
  become: yes

- name: Установка PostgreSQL
  apt:
    name:
      - "postgresql"
      - "postgresql-contrib"
    state: present

- name: Создать каталог данных для PostgreSQL на внешнем диске
  file:
    path: "{{ postgresql_data_directory }}"
    state: directory
    owner: postgres
    group: postgres
    mode: '0700'
  become: yes

- name: Обновить конфигурацию PostgreSQL для использования нового каталога данных
  lineinfile:
    path: "/etc/postgresql/16/main/postgresql.conf"
    regexp: '^data_directory ='
    line: "data_directory = '{{ postgresql_data_directory }}'"
  notify: Перезапустить PostgreSQL
  become: yes

- name: Инициализация кластера базы данных в новом каталоге (если пустой)
  command: "/usr/lib/postgresql/16/bin/initdb -D {{ postgresql_data_directory }}"
  args:
    creates: "{{ postgresql_data_directory }}/PG_VERSION"
  become: yes
  become_user: postgres
  when: postgresql_data_directory is defined

- name: Убедиться, что PostgreSQL запущен и включен
  service:
    name: postgresql
    state: started
    enabled: true

- name: Создание временного каталога для Ansible в домашней директории пользователя postgres
  file:
    path: /var/lib/postgresql/.ansible/tmp
    state: directory
    owner: postgres
    group: postgres
    mode: '0700'
  become: yes

- name: Создание базы данных
  become_user: postgres
  postgresql_db:
    name: "{{ postgresql_database }}"
    encoding: "{{ postgresql_encoding }}"
    lc_collate: "{{ postgresql_locale }}"
    lc_ctype: "{{ postgresql_locale }}"
    state: present

- name: Создание пользователя базы данных
  become_user: postgres
  community.postgresql.postgresql_user:
    name: "{{ postgresql_user }}"
    password: "{{ postgresql_password }}"
    state: present

- name: Назначение привилегий пользователю на базу данных
  become_user: postgres
  community.postgresql.postgresql_privs:
    db: "{{ postgresql_database }}"
    type: database
    privs: "ALL"
    roles: "{{ postgresql_user }}"
    state: present



#### vars

- **main.yml**

$ANSIBLE_VAULT;1.1;AES256
66333834373638663037343436643136343539343861626565393137393431623639323136333036
3037343061333766376339396136373461633934323337310a613861343035653465616331383065
33663237373535386361323433366637373632613863313637313561626435633663343561663034
3332383763333261660a663339653062333635633435313035333537653932623337326532373637
61373439363230366461363537393135643466656437383562303434636339313738646438323966
33376466366162653831666632363335323266346330613136363234633266626333663738616636
37313137353832656661306633363438623436396534643437326231626134383135333863323663
30636664393431613762633233666663643063366338326137363664366239356330663533303131
61623764353839643364613239383166666539316133356661666366363535633538636234366438
39646632323835616538646230646561343364623537633333393838363935393635616435663662
33336462663566313261353238616236633261613435346233303766666239653737373031373036
63393033666233353438343934623430333937353236373938353534643766303034663265653539
37366263646636636433333562643063633938313363393864356566373232326236393065386462
35333532626438303437393734646264373464356532353431346432383739323938306532323766
65316538333966306561346332313239643730303163313934383061336337316130623434366139
37353861376665613566393964363034373232313530383764353038646563356166636262303731
6535


### prometheus

#### tasks

- **main.yml**

---
- name: Установка Prometheus
  apt:
    name: prometheus
    state: present

- name: Убедиться, что Prometheus запущен и включен
  systemd:
    name: prometheus
    enabled: true
    state: started

- name: Настройка firewall для Prometheus
  ufw:
    rule: allow
    port: '9090'
    proto: tcp
    state: enabled


#### templates

- **prometheus.yml.j2**



#### vars

- **main.yml**



### ufw

#### handler

#### tasks

- **main.yml**

---
- name: Проверить, установлен ли ufw
  apt:
    name: ufw
    state: present
  register: ufw_installed

- debug:
    msg: "UFW установлен"

- name: Разрешить SSH (порт 22) в ufw
  ufw:
    rule: allow
    port: '22'
    proto: tcp

- name: Разрешить HTTP (порт 80) в ufw
  ufw:
    rule: allow
    port: '80'
    proto: tcp

- name: Разрешить HTTPS (порт 443) в ufw
  ufw:
    rule: allow
    port: '443'
    proto: tcp

- name: Разрешить PostgreSQL (порт 5432) в ufw
  ufw:
    rule: allow
    port: '5432'
    proto: tcp

- name: Включить и перезапустить ufw
  ufw:
    state: enabled


