package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.User;
import com.tangdyn.tijian.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Autowired
    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public User registerUser(User user) {
        // 加密密码
        String encryptedPassword = passwordEncoder.encode(user.getPassword());
        user.setPassword(encryptedPassword);

        // 设置默认的 userType 为 1 如果用户没有指定 userType
        if (user.getUserType() == null) {
            user.setUserType(1);
        }

        // 保存用户
        return userRepository.save(user);
    }

    public User getUserByUserID(String userID) {
        Optional<User> optionalUser = userRepository.findByUserID(userID);
        return optionalUser.orElse(null);
    }
}
