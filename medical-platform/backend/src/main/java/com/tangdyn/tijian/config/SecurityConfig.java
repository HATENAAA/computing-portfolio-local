package com.tangdyn.tijian.config;

import jakarta.servlet.DispatcherType;
import com.tangdyn.tijian.filter.JwtAuthenticationFilter;
import com.tangdyn.tijian.service.CustomUserDetailsService;
import com.tangdyn.tijian.util.JwtAuthenticationEntryPoint;
import com.tangdyn.tijian.util.JwtTokenUtil;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {
    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http, JwtAuthenticationEntryPoint unauthorized,
                                            JwtTokenUtil tokens) throws Exception {
        return http.csrf(AbstractHttpConfigurer::disable)
                .exceptionHandling(config -> config.authenticationEntryPoint(unauthorized))
                .sessionManagement(config -> config.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(routes -> routes
                        .dispatcherTypeMatchers(DispatcherType.ERROR).permitAll()
                        .requestMatchers("/", "/index.html", "/favicon.ico", "/css/**", "/js/**",
                                "/fonts/**", "/img/**", "/doctor.html", "/doctor.css", "/doctor.js", "/clinic.png",
                                "/api/health", "/users/login", "/users/register", "/users/verify_token",
                                "/doctor/getDoctorByCodeByPass").permitAll()
                        .requestMatchers("/doctor/**", "/ciDetailedReport/updateCiDetailedReport").hasRole("DOCTOR")
                        .anyRequest().hasRole("USER"))
                .addFilterBefore(new JwtAuthenticationFilter(tokens), UsernamePasswordAuthenticationFilter.class)
                .build();
    }

    @Bean
    DaoAuthenticationProvider authenticationProvider(CustomUserDetailsService users, PasswordEncoder passwords) {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        provider.setUserDetailsService(users);
        provider.setPasswordEncoder(passwords);
        return provider;
    }

    @Bean
    AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }
}
