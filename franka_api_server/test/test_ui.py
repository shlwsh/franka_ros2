import pytest
from playwright.sync_api import Page, expect

def test_dashboard_load(page: Page, api_server_url):
    """Test that the dashboard loads successfully and displays the correct title"""
    page.goto(api_server_url)
    expect(page).to_have_title("Franka API Dashboard")
    
    # Check if main UI elements are present
    expect(page.locator("text=Dashboard Overview")).to_be_visible()
    
    # Make sure we're on the dashboard view
    expect(page.locator("#dashboard-view")).to_have_class("view active")
    
    # Set the test API key into the input
    page.fill("#api-key-input", "test-secret-key")

def test_sidebar_navigation(page: Page, api_server_url):
    """Test navigating through different sections via the sidebar"""
    page.goto(api_server_url)
    
    # Click Motion Control
    page.click("a[data-target='motion-view']")
    expect(page.locator("#motion-view")).to_have_class("view active")
    expect(page.locator("#dashboard-view")).not_to_have_class("view active")
    
    # Click Gripper
    page.click("a[data-target='gripper-view']")
    expect(page.locator("#gripper-view")).to_have_class("view active")
    
    # Click Controllers
    page.click("a[data-target='controllers-view']")
    expect(page.locator("#controllers-view")).to_have_class("view active")

def test_motion_slider_interaction(page: Page, api_server_url):
    """Test interacting with sliders in the Motion Control view"""
    page.goto(api_server_url)
    page.click("a[data-target='motion-view']")
    
    # Interact with the velocity scaling slider
    slider = page.locator("#vel-scale")
    # Using JS to set value since it's an input type=range
    slider.evaluate("el => { el.value = 0.85; el.dispatchEvent(new Event('input')) }")
    
    # Assert the displayed text updated correctly
    expect(page.locator("#vel-scale-val")).to_have_text("0.85")

def test_api_tester_interaction(page: Page, api_server_url):
    """Test the built-in API tester sends requests and gets responses"""
    page.goto(api_server_url)
    
    # Set correct API key for tests
    page.fill("#api-key-input", "test-secret-key")
    
    page.click("a[data-target='api-tester-view']")
    
    # Default is GET /api/v1/status/joints
    page.click("#btn-send-api")
    
    # Wait for the response to load (we check if 'Status: 200' appears)
    response_area = page.locator("#api-response")
    expect(response_area).to_contain_text("Status: 200", timeout=5000)
    
def test_controllers_list_refresh(page: Page, api_server_url):
    """Test fetching the controllers list via UI"""
    page.goto(api_server_url)
    page.fill("#api-key-input", "test-secret-key")
    page.click("a[data-target='controllers-view']")
    
    page.click("#btn-refresh-ctrl")
    
    # Wait for the table to populate
    row = page.locator("#controllers-table tbody tr").first
    expect(row).to_be_visible(timeout=5000)
    expect(row).to_contain_text("joint_state_broadcaster")
