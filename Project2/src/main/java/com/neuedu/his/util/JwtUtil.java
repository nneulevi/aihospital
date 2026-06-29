package com.neuedu.his.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component  // 加上 @Component，支持注入
public class JwtUtil {

    private static final String SECRET_KEY = "his-secret-key-2024-neuedu-healthcare-system";
    private static final long EXPIRATION_TIME = 86400000L;

    private static SecretKey getSigningKey() {
        byte[] keyBytes = SECRET_KEY.getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    // ========== 静态方法（已有，保持不变） ==========

    public static String generateToken(Integer userId, String username, String roleType) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        claims.put("roleType", roleType);

        return Jwts.builder()
                .claims(claims)
                .subject(username)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
                .signWith(getSigningKey())
                .compact();
    }

    public static String generatePatientToken(String phone) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", 0);
        claims.put("username", phone);
        claims.put("roleType", "PATIENT");

        return Jwts.builder()
                .claims(claims)
                .subject(phone)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
                .signWith(getSigningKey())
                .compact();
    }

    public static Claims parseToken(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public static Integer getUserIdFromToken(String token) {
        Claims claims = parseToken(token);
        return claims.get("userId", Integer.class);
    }

    public static String getUsernameFromToken(String token) {
        Claims claims = parseToken(token);
        return claims.get("username", String.class);
    }

    public static String getRoleTypeFromToken(String token) {
        Claims claims = parseToken(token);
        return claims.get("roleType", String.class);
    }

    // ========== 新增：实例方法（用于 Service 注入调用） ==========

    /**
     * 生成 Token（简化版，用于患者注册登录）
     */
    public String generateToken(Integer userId, String userType) {
        return generateToken(userId, "user_" + userId, userType);
    }

    /**
     * 验证 Token 是否有效
     */
    public boolean validateToken(String token) {
        try {
            parseToken(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}