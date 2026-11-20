package com.hystu.springboot_.controller;

import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.*;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class Errors {

  @ExceptionHandler(DataIntegrityViolationException.class)
  public ResponseEntity<?> conflict() {
    return ResponseEntity.status(409).body(
      Map.of(
        "error",
        "Duplicate value, referenced resource, or invalid data constraint"
      )
    );
  }

  @ExceptionHandler(AccessDeniedException.class)
  public ResponseEntity<?> denied() {
    return ResponseEntity.status(403).body(
      Map.of("error", "Operation not permitted")
    );
  }

  @ExceptionHandler(ResponseStatusException.class)
  public ResponseEntity<?> status(ResponseStatusException e) {
    return ResponseEntity.status(e.getStatusCode()).body(
      Map.of(
        "error",
        e.getReason() == null ? "Request rejected" : e.getReason()
      )
    );
  }

  @ExceptionHandler(HttpMessageNotReadableException.class)
  public ResponseEntity<?> malformed() {
    return ResponseEntity.badRequest().body(
      Map.of("error", "Invalid request body")
    );
  }
}
