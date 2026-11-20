package com.hystu.springboot_.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hystu.springboot_.mapper.UserMapper;
import org.springframework.context.annotation.*;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.*;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

  @Bean
  PasswordEncoder passwords() {
    return new BCryptPasswordEncoder();
  }

  @Bean
  UserDetailsService details(UserMapper users) {
    return name -> {
      var u = users.findByUsername(name);
      if (u == null) throw new UsernameNotFoundException("Invalid credentials");
      return User.withUsername(u.getUsername())
        .password(u.getPassword())
        .roles(u.getRole())
        .build();
    };
  }

  @Bean
  SecurityFilterChain security(
    HttpSecurity http,
    UserMapper users,
    ObjectMapper json
  ) throws Exception {
    http
      .authorizeHttpRequests(a ->
        a
          .requestMatchers("/auth/csrf", "/auth/demo", "/users/registerUser", "/error")
          .permitAll()
          .anyRequest()
          .authenticated()
      )
      .exceptionHandling(e ->
        e.authenticationEntryPoint((req, res, ex) -> {
          res.setStatus(401);
          res.setContentType("application/json");
          res.getWriter().write("{\"error\":\"Login required\"}");
        })
      )
      .formLogin(f ->
        f
          .loginProcessingUrl("/users/login")
          .successHandler((req, res, auth) -> {
            res.setContentType("application/json");
            json.writeValue(
              res.getOutputStream(),
              users.findByUsername(auth.getName())
            );
          })
          .failureHandler((req, res, ex) -> {
            res.setStatus(401);
            res.setContentType("application/json");
            res.getWriter().write("{\"error\":\"Invalid credentials\"}");
          })
          .permitAll()
      )
      .logout(l ->
        l
          .logoutUrl("/users/logout")
          .logoutSuccessHandler((req, res, auth) -> res.setStatus(204))
      );
    return http.build();
  }
}
