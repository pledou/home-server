external_url 'https://gitlab.{{app_domain_name}}/'
gitlab_rails['initial_root_password'] = File.read('/run/secrets/gitlab_root_password')

letsencrypt['enable'] = false

nginx['listen_port'] = 8181
nginx['listen_https'] = false
nginx['http2_enabled'] = false

nginx['proxy_set_headers'] = {
  "Host" => "$http_host",
  "X-Real-IP" => "$remote_addr",
  "X-Forwarded-For" => "$proxy_add_x_forwarded_for",
  "X-Forwarded-Proto" => "https",
  "X-Forwarded-Ssl" => "on"
}

gitlab_rails['gitlab_shell_ssh_port'] = 22

registry_external_url 'https://registry.gitlab.{{app_domain_name}}'
registry_nginx['listen_port'] = 5100
registry_nginx['listen_https'] = false
registry_nginx['proxy_set_headers'] = {
  "Host" => "$http_host",
  "X-Real-IP" => "$remote_addr",
  "X-Forwarded-For" => "$proxy_add_x_forwarded_for",
  "X-Forwarded-Proto" => "https",
  "X-Forwarded-Ssl" => "on"
}

pages_external_url 'https://pages.gitlab.{{app_domain_name}}'
pages_nginx['listen_port'] = 5200
pages_nginx['listen_https'] = false

pages_nginx['proxy_set_headers'] = {
  "Host" => "$http_host",
  "X-Real-IP" => "$remote_addr",
  "X-Forwarded-For" => "$proxy_add_x_forwarded_for",
  "X-Forwarded-Proto" => "https",
  "X-Forwarded-Ssl" => "on"
}

gitlab_pages['inplace_chroot'] = true
gitlab_pages['external_http'] = ['gitlab:5201']

gitlab_rails['smtp_enable'] = true
gitlab_rails['smtp_address'] = "{{ kresus_email_host }}"
gitlab_rails['smtp_port'] = {{ kresus_email_port }}
gitlab_rails['smtp_user_name'] = "{{ kresus_email_user }}"
gitlab_rails['smtp_password'] = "{{ kresus_email_password }}"
gitlab_rails['smtp_authentication'] = "login"
gitlab_rails['smtp_enable_starttls_auto'] = true