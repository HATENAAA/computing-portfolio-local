package com.tangdyn.tijian.util;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import java.security.Key;
import java.time.Instant;
import java.util.Date;

@Component
public class JwtTokenUtil {
    private final Key signingKey = Keys.secretKeyFor(SignatureAlgorithm.HS256);

    public String generateToken(String subject) {
        Instant now = Instant.now();
        return Jwts.builder().setSubject(subject).setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(14_400))).signWith(signingKey).compact();
    }

    public String getUserIDFromToken(String token) {
        return Jwts.parserBuilder().setSigningKey(signingKey).build()
                .parseClaimsJws(token).getBody().getSubject();
    }
}
