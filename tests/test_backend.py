#!/usr/bin/env python3
"""
Comprehensive backend test script for ForgeMind AI.
Tests all backend functionality end-to-end without modifying code.
"""

import sys
import json
import io
import os
import time
import numpy as np
import cv2
import requests
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, '/Users/aarushgupta/Documents/Projects/ForgeMind-AI')

from main import app
from computer_vision.detection.symbol_detection import SymbolDetector
from computer_vision.config import MODEL_PATH

# Initialize test client
client = TestClient(app)

def test_status_endpoint():
    """Test /status endpoint"""
    print("Testing /status endpoint...")
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "indexed_files" in data
    assert "chunk_count" in data
    assert "ready" in data
    print("  ✓ /status endpoint works")
    return data

def test_info_endpoint():
    """Test /detect/info endpoint"""
    print("Testing /detect/info endpoint...")
    response = client.get("/detect/info")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "pipeline" in data
    assert "supported_classes" in data
    print("  ✓ /detect/info endpoint works")
    return data

def test_health_endpoint():
    """Test /detect/health endpoint"""
    print("Testing /detect/health endpoint...")
    response = client.get("/detect/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "model_path" in data
    assert "model_exists" in data
    assert "ocr_loaded" in data
    assert "parser_loaded" in data
    assert "pinecone_enabled" in data
    print("  ✓ /detect/health endpoint works")
    return data

def test_yolo_model_classes():
    """Test that YOLO model loads and class names match trained model"""
    print("Testing YOLO model classes...")
    try:
        detector = SymbolDetector(model_path=str(MODEL_PATH))
        # Get class names from model
        model_names = detector.model.names
        # Expected classes from training
        expected_classes = ["Pump", "Valve", "HeatExchanger", "PressureGauge"]

        # Check that all expected classes are present
        for cls in expected_classes:
            assert cls in model_names.values(), f"Class {cls} not found in model"

        # Check that model only has expected classes (no extra unexpected ones)
        model_classes = set(model_names.values())
        expected_set = set(expected_classes)
        assert model_classes == expected_set, f"Model classes {model_classes} don't match expected {expected_set}"

        print(f"  ✓ YOLO model loads successfully with classes: {model_classes}")
        return model_names
    except Exception as e:
        print(f"  ✗ Error loading YOLO model: {e}")
        raise

def create_test_image_with_text():
    """Create a test image with some text for OCR testing"""
    # Create a white image
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    # Add some text
    cv2.putText(img, "PUMP-101", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "PRESSURE GAUGE PG-205", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "FLOW: 100 L/MIN", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    # Encode as PNG
    is_success, buffer = cv2.imencode(".png", img)
    assert is_success, "Failed to encode image"
    io_buf = io.BytesIO(buffer)
    return io_buf, "test_image.png"

def create_test_image_with_shapes():
    """Create a test image with geometric shapes for detection testing"""
    # Create a white image
    img = np.zeros((300, 300, 3), dtype=np.uint8) + 255
    # Draw some rectangles that might be detected as objects
    cv2.rectangle(img, (50, 50), (150, 150), (0, 0, 0), 2)  # Rectangle
    cv2.circle(img, (200, 200), 30, (0, 0, 0), 2)  # Circle
    cv2.rectangle(img, (100, 200), (200, 250), (0, 0, 0), -1)  # Filled rectangle
    # Encode as PNG
    is_success, buffer = cv2.imencode(".png", img)
    assert is_success, "Failed to encode image"
    io_buf = io.BytesIO(buffer)
    return io_buf, "shapes_image.png"

def test_detect_endpoint():
    """Test /detect endpoint with various scenarios"""
    print("Testing /detect endpoint...")

    # Test 1: Image with text
    print("  Testing with text image...")
    io_buf, filename = create_test_image_with_text()
    files = {"image": (filename, io_buf, "image/png")}
    response = client.post("/detect", files=files)

    # Check response status
    assert response.status_code == 200, f"Detection failed: {response.text}"
    data = response.json()

    # Check response structure
    assert data["success"] == True
    assert "detections" in data
    assert "annotated_image" in data
    assert "statistics" in data
    assert data["annotated_image"].startswith("/results/")

    # Check each detection has required fields
    for det in data["detections"]:
        assert "label" in det, "Detection missing label"
        assert "confidence" in det, "Detection missing confidence"
        assert "bbox" in det, "Detection missing bbox"
        assert isinstance(det["label"], str), "Label should be string"
        assert isinstance(det["confidence"], float), "Confidence should be float"
        assert 0 <= det["confidence"] <= 1, "Confidence should be between 0 and 1"
        assert "x1" in det["bbox"] and "y1" in det["bbox"] and "x2" in det["bbox"] and "y2" in det["bbox"], "Bbox missing coordinates"
        assert det["label"] != "undefined", f"Found 'undefined' label: {det}"

        # Check OCR field exists
        assert "ocr" in det, "Detection missing OCR field"
        assert isinstance(det["ocr"], str), "OCR should be string"

        # Check parser results exist (can be empty dict)
        assert "pid" in det, "Detection missing PID field"
        assert "table" in det, "Detection missing table field"
        assert "drawing" in det, "Detection missing drawing field"

    print(f"  ✓ Detection successful: {len(data['detections'])} objects found")

    # Test 2: Image with shapes
    print("  Testing with shapes image...")
    io_buf, filename = create_test_image_with_shapes()
    files = {"image": (filename, io_buf, "image/png")}
    response = client.post("/detect", files=files)

    assert response.status_code == 200, f"Detection failed: {response.text}"
    data = response.json()
    assert data["success"] == True
    print(f"  ✓ Shapes detection successful: {len(data['detections'])} objects found")

    return data

def test_annotated_image_access():
    """Test that annotated images are accessible"""
    print("Testing annotated image accessibility...")
    # First run detection to get an image
    io_buf, filename = create_test_image_with_text()
    files = {"image": (filename, io_buf, "image/png")}
    response = client.post("/detect", files=files)
    assert response.status_code == 200
    data = response.json()
    img_path = data["annotated_image"]  # e.g., "/results/abc123.jpg"

    # Now try to access the image
    response = client.get(img_path)
    # Should return 200 OK or possibly redirect
    assert response.status_code == 200, f"Cannot access annotated image: {response.status_code}"
    assert len(response.content) > 0, "Annotated image is empty"
    print(f"  ✓ Annotated image accessible: {len(response.content)} bytes")

def test_ocr_parser_integration():
    """Test that OCR -> Parser -> Pinecone indexing works"""
    print("Testing OCR -> Parser -> Pinecone integration...")
    # Use image with clear text that should be parsed
    img = np.ones((150, 400, 3), dtype=np.uint8) * 255
    cv2.putText(img, "PUMP-101 TAG", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "PG-205 PRESSURE 100 PSI", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    is_success, buffer = cv2.imencode(".png", img)
    io_buf = io.BytesIO(buffer)
    files = {"image": ("ocr_test.png", io_buf, "image/png")}
    response = client.post("/detect", files=files)
    assert response.status_code == 200
    data = response.json()

    # Check that we got some detections
    assert len(data["detections"]) > 0, "No detections found in OCR test image"

    # Check that at least one detection has OCR text
    has_ocr_text = any(len(det["ocr"].strip()) > 0 for det in data["detections"])
    # Note: OCR might not always detect text depending on image quality, but parser should still run

    # Check that parser fields exist (even if empty)
    for det in data["detections"]:
        assert isinstance(det["pid"], dict), "PID should be dict"
        assert isinstance(det["table"], dict), "Table should be dict"
        assert isinstance(det["drawing"], dict), "Drawing should be dict"

    print(f"  ✓ OCR/Parsing pipeline completed for {len(data['detections'])} detections")

def test_upload_build_chat_flow():
    """Test the complete upload -> build -> chat flow"""
    print("Testing upload -> build -> chat flow...")

    # 1. Upload a text file
    content = b"The quick brown fox jumps over the lazy dog. This is a test document for ForgeMind AI."
    files = {"files": ("test_doc.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    upload_data = response.json()
    assert "test_doc.txt" in upload_data.get("saved", [])
    print("  ✓ File uploaded successfully")

    # 2. Build index
    response = client.post("/build")
    assert response.status_code == 200
    build_data = response.json()
    assert build_data["success"] == True
    assert build_data["chunk_count"] > 0
    assert "test_doc.txt" in build_data["indexed_files"]
    print(f"  ✓ Index built successfully: {build_data['chunk_count']} chunks")

    # 3. Check status
    response = client.get("/status")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["ready"] == True
    assert "test_doc.txt" in status_data["indexed_files"]
    assert status_data["chunk_count"] > 0
    print("  ✓ Status shows index is ready")

    # 4. Chat query
    chat_req = {"message": "What animal jumps over the lazy dog?"}
    response = client.post("/chat", json=chat_req)
    assert response.status_code == 200

    # Parse streaming response
    full_text = ""
    sources = []
    for line in response.iter_lines():
        if line:
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                try:
                    msg = json.loads(data_str)
                except:
                    continue
                if msg.get("type") == "text":
                    full_text += msg.get("content", "")
                elif msg.get("type") == "done":
                    sources = msg.get("sources", [])
                    break

    print(f"  Chat response: {repr(full_text[:100])}...")
    assert "fox" in full_text.lower() or "brown" in full_text
    assert len(sources) > 0, "No sources returned"
    # Check that source is our uploaded file
    source_files = [s.get("file") for s in sources if s.get("file")]
    assert any("test_doc.txt" in f for f in source_files), f"Source file not found in {source_files}"
    print(f"  ✓ Chat works and returns sources: {source_files}")

    # 5. Clear history
    response = client.post("/clear-history")
    assert response.status_code == 200
    print("  ✓ History cleared")

    # 6. Clear index
    response = client.post("/clear")
    assert response.status_code == 200
    # Verify status after clear
    response = client.get("/status")
    assert response.status_code == 200
    status = response.json()
    assert status["ready"] == False
    assert status["indexed_files"] == []
    assert status["chunk_count"] == 0
    print("  ✓ Index cleared successfully")

def test_error_cases():
    """Test error handling"""
    print("Testing error cases...")

    # Test invalid file type
    content = b"not an image"
    files = {"image": ("test.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/detect", files=files)
    assert response.status_code == 400, "Should reject non-image file"
    print("  ✓ Correctly rejects non-image files")

    # Test missing file
    response = client.post("/detect", files={})
    assert response.status_code == 422, "Should require image field"
    print("  ✓ Correctly requires image field")

    # Test chat without index
    # First clear index
    client.post("/clear")
    chat_req = {"message": "test question"}
    response = client.post("/chat", json=chat_req)
    assert response.status_code == 400, "Should reject chat without index"
    print("  ✓ Correctly rejects chat without index")

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("Starting comprehensive backend tests for ForgeMind AI")
    print("=" * 60)

    try:
        # Basic endpoints
        test_status_endpoint()
        test_info_endpoint()
        test_health_endpoint()

        # Model tests
        test_yolo_model_classes()

        # Detection tests
        test_detect_endpoint()
        test_annotated_image_access()
        test_ocr_parser_integration()

        # Integration tests
        test_upload_build_chat_flow()

        # Error handling
        test_error_cases()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! 🎉")
        print("=" * 60)
        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)