package com.neuedu.his.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

public class JwtUtil {
    private static final String SECRET_KEY = "his-secret-key-2024-neuedu-healthcare-system";
    private static final long EXPIRATION_TIME = 86400000L;

    private static SecretKey getSigningKey() {
        byte[] keyBytes = SECRET_KEY.getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

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
        return generatePatientToken(0, phone, null);
    }

    public static String generatePatientToken(Integer patientId, String phone, String caseNumber) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", patientId == null ? 0 : patientId);
        claims.put("patientId", patientId == null ? 0 : patientId);
        claims.put("username", phone);
        claims.put("phone", phone);
        claims.put("caseNumber", caseNumber);
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
}
