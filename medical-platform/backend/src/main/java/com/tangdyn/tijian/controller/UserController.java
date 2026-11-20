package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.User;
import com.tangdyn.tijian.service.CustomUserDetailsService;
import com.tangdyn.tijian.service.UserService;
import com.tangdyn.tijian.util.JwtTokenUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.Map;

@RestController
@RequestMapping("/users")
public class UserController {
    private final UserService userService;
    private final JwtTokenUtil jwtTokenUtil;
    private final AuthenticationManager authenticationManager;
    private final CustomUserDetailsService customUserDetailsService;

    @Autowired
    public UserController(UserService userService, JwtTokenUtil jwtTokenUtil, AuthenticationManager authenticationManager, CustomUserDetailsService customUserDetailsService) {
        this.userService = userService;
        this.jwtTokenUtil = jwtTokenUtil;
        this.authenticationManager = authenticationManager;
        this.customUserDetailsService = customUserDetailsService;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody User user) {
        try {
            authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(user.getUserID(), user.getPassword()));
            String accessToken = jwtTokenUtil.generateToken(user.getUserID());
            return ResponseEntity.ok(accessToken); // 登录成功，生成JWT令牌
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Invalid credentials");
        }
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        user.setUserType(1);
        if (user.getUserID() == null || !user.getUserID().matches("[0-9]{11}") || user.getPassword() == null || user.getPassword().length() < 8 || user.getPassword().getBytes(java.nio.charset.StandardCharsets.UTF_8).length > 72 || user.getRealName() == null || user.getRealName().isBlank() || user.getRealName().length() > 20 || user.getIdentityCard() == null || !user.getIdentityCard().matches("[0-9]{17}[0-9Xx]") || user.getBirthday() == null || user.getSex() == null) {
            return ResponseEntity.badRequest().body("请检查注册信息，密码至少八个字符。");
        }
        if (userService.getUserByUserID(user.getUserID()) != null) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body("This Phone Number has been registered");
        }
        userService.registerUser(user);
        return ResponseEntity.status(HttpStatus.CREATED).body("Create successful");
    }

    @GetMapping("/getUserByUserID")
    public ResponseEntity<?> getUserByUserID(@RequestParam String userID, Principal principal) {
        if (!userID.equals(principal.getName())) return ResponseEntity.notFound().build();
        User user = userService.getUserByUserID(userID);
        if (user == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("User Not Found");
        }
        return ResponseEntity.ok(user);
    }

    @PostMapping("/verify_token")
    public ResponseEntity<?> verifyToken(@RequestBody Map<String, String> request) {
        String token = request.get("token");
        if (token == null || token.trim().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Token is required");
        }

        try {
            String userID = jwtTokenUtil.getUserIDFromToken(token);
            customUserDetailsService.loadUserByUsername(userID);
            return ResponseEntity.ok("Token is valid");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Token is invalid");
        }
    }
}
