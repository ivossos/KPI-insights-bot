/**
 * Apify Actor for scraping Betha portals (folha, despesas, contratos)
 * Handles automated CSV export from municipal transparency portals
 */

const Apify = require('apify');
const puppeteer = require('puppeteer');

// Configuration
const PORTALS = {
    folha: {
        url: 'https://folha.betha.cloud/transparency/capivari',
        csvSelector: '.export-csv-button',
        waitForSelector: '.data-table',
        dataType: 'folha'
    },
    despesas: {
        url: 'https://despesas.betha.cloud/transparency/capivari',
        csvSelector: '.export-csv-button',
        waitForSelector: '.data-table',
        dataType: 'despesas'
    },
    contratos: {
        url: 'https://contratos.betha.cloud/transparency/capivari',
        csvSelector: '.export-csv-button',
        waitForSelector: '.data-table',
        dataType: 'contratos'
    }
};

const WEBHOOK_URL = 'https://your-replit-app.repl.co/webhook/ingestion';
const WEBHOOK_SECRET = 'your-webhook-secret';

Apify.main(async () => {
    console.log('Starting Betha portals scraper...');
    
    // Get input parameters
    const input = await Apify.getInput() || {};
    const { portals = Object.keys(PORTALS), maxRetries = 3 } = input;
    
    // Initialize browser
    const browser = await puppeteer.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    });
    
    const results = [];
    
    try {
        // Process each portal
        for (const portalName of portals) {
            if (!PORTALS[portalName]) {
                console.warn(`Unknown portal: ${portalName}`);
                continue;
            }
            
            const portalConfig = PORTALS[portalName];
            console.log(`Processing portal: ${portalName}`);
            
            let success = false;
            let lastError = null;
            
            // Retry logic
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    const result = await scrapePortal(browser, portalName, portalConfig);
                    
                    if (result.success) {
                        success = true;
                        results.push(result);
                        break;
                    }
                    
                } catch (error) {
                    lastError = error;
                    console.error(`Attempt ${attempt} failed for ${portalName}:`, error.message);
                    
                    if (attempt < maxRetries) {
                        console.log(`Retrying in 5 seconds...`);
                        await new Promise(resolve => setTimeout(resolve, 5000));
                    }
                }
            }
            
            if (!success) {
                console.error(`Failed to scrape ${portalName} after ${maxRetries} attempts`);
                results.push({
                    portal: portalName,
                    success: false,
                    error: lastError ? lastError.message : 'Unknown error',
                    timestamp: new Date().toISOString()
                });
            }
            
            // Wait between portals to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Send results to webhook
        await sendWebhookNotification(results);
        
    } catch (error) {
        console.error('Actor execution failed:', error);
        throw error;
    } finally {
        await browser.close();
    }
    
    // Save results to Apify dataset
    await Apify.pushData({
        timestamp: new Date().toISOString(),
        portals: results,
        summary: {
            total: results.length,
            successful: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length
        }
    });
    
    console.log('Scraping completed');
});

async function scrapePortal(browser, portalName, config) {
    const page = await browser.newPage();
    
    try {
        // Set viewport and user agent
        await page.setViewport({ width: 1920, height: 1080 });
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // Navigate to portal
        console.log(`Navigating to ${config.url}...`);
        await page.goto(config.url, { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        // Wait for page to load
        await page.waitForSelector(config.waitForSelector, { timeout: 20000 });
        
        // Handle any date filters (set to current month)
        await setDateFilters(page);
        
        // Wait for data to load
        await page.waitForTimeout(3000);
        
        // Check if data table has content
        const hasData = await page.evaluate((selector) => {
            const table = document.querySelector(selector);
            return table && table.rows && table.rows.length > 1;
        }, config.waitForSelector);
        
        if (!hasData) {
            console.warn(`No data found in ${portalName}`);
        }
        
        // Click export CSV button
        console.log(`Clicking CSV export button...`);
        await page.click(config.csvSelector);
        
        // Wait for download to start
        await page.waitForTimeout(2000);
        
        // Check if export was successful
        const exportSuccess = await checkExportSuccess(page);
        
        if (!exportSuccess) {
            throw new Error('CSV export failed - no download detected');
        }
        
        // Get the download URL or file content
        const csvData = await getCsvData(page);
        
        // Save to Apify dataset
        const dataset = await Apify.openDataset(`${portalName}-csv-data`);
        await dataset.pushData({
            portal: portalName,
            dataType: config.dataType,
            timestamp: new Date().toISOString(),
            recordCount: csvData.recordCount,
            csvContent: csvData.content
        });
        
        console.log(`Successfully scraped ${portalName}: ${csvData.recordCount} records`);
        
        return {
            portal: portalName,
            success: true,
            dataType: config.dataType,
            recordCount: csvData.recordCount,
            timestamp: new Date().toISOString(),
            datasetId: dataset.id
        };
        
    } catch (error) {
        console.error(`Error scraping ${portalName}:`, error);
        throw error;
    } finally {
        await page.close();
    }
}

async function setDateFilters(page) {
    try {
        // Set date range to current month
        const currentDate = new Date();
        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        
        const formatDate = (date) => {
            return date.toLocaleDateString('pt-BR').split('/').reverse().join('-');
        };
        
        // Look for date input fields
        const dateFromSelector = 'input[name="dateFrom"], input[id="dateFrom"], .date-from';
        const dateToSelector = 'input[name="dateTo"], input[id="dateTo"], .date-to';
        
        // Set start date
        const dateFromElement = await page.$(dateFromSelector);
        if (dateFromElement) {
            await dateFromElement.click({ clickCount: 3 });
            await dateFromElement.type(formatDate(firstDay));
        }
        
        // Set end date
        const dateToElement = await page.$(dateToSelector);
        if (dateToElement) {
            await dateToElement.click({ clickCount: 3 });
            await dateToElement.type(formatDate(lastDay));
        }
        
        // Apply filters
        const applyButton = await page.$('.apply-filters, .btn-apply, button[type="submit"]');
        if (applyButton) {
            await applyButton.click();
            await page.waitForTimeout(2000);
        }
        
    } catch (error) {
        console.warn('Could not set date filters:', error.message);
    }
}

async function checkExportSuccess(page) {
    try {
        // Wait for potential download indicators
        await page.waitForTimeout(3000);
        
        // Check for success messages
        const successIndicators = [
            '.export-success',
            '.download-ready',
            '.alert-success',
            '[data-export-status="success"]'
        ];
        
        for (const selector of successIndicators) {
            const element = await page.$(selector);
            if (element) {
                return true;
            }
        }
        
        // Check for download links
        const downloadLink = await page.$('a[href*=".csv"], a[download*=".csv"]');
        if (downloadLink) {
            return true;
        }
        
        return false;
        
    } catch (error) {
        console.warn('Could not verify export success:', error.message);
        return false;
    }
}

async function getCsvData(page) {
    try {
        // Method 1: Download link
        const downloadLink = await page.$('a[href*=".csv"], a[download*=".csv"]');
        if (downloadLink) {
            const href = await downloadLink.evaluate(el => el.href);
            const response = await page.goto(href);
            const content = await response.text();
            
            return {
                content: content,
                recordCount: content.split('\n').length - 1
            };
        }
        
        // Method 2: Direct table extraction
        const tableData = await page.evaluate(() => {
            const table = document.querySelector('.data-table, table');
            if (!table) return null;
            
            const rows = Array.from(table.rows);
            const csvLines = [];
            
            rows.forEach(row => {
                const cells = Array.from(row.cells);
                const line = cells.map(cell => {
                    let text = cell.textContent.trim();
                    // Escape quotes and handle commas
                    if (text.includes('"')) {
                        text = text.replace(/"/g, '""');
                    }
                    if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                        text = `"${text}"`;
                    }
                    return text;
                }).join(',');
                
                csvLines.push(line);
            });
            
            return csvLines.join('\n');
        });
        
        if (tableData) {
            return {
                content: tableData,
                recordCount: tableData.split('\n').length - 1
            };
        }
        
        throw new Error('Could not extract CSV data');
        
    } catch (error) {
        console.error('Error getting CSV data:', error);
        throw error;
    }
}

async function sendWebhookNotification(results) {
    try {
        const crypto = require('crypto');
        
        for (const result of results) {
            if (result.success) {
                const webhookData = {
                    dataset_id: result.datasetId,
                    dataset_type: result.dataType,
                    run_id: process.env.APIFY_RUN_ID,
                    status: 'SUCCEEDED',
                    items_count: result.recordCount,
                    download_url: `https://api.apify.com/v2/datasets/${result.datasetId}/items?format=csv`,
                    timestamp: result.timestamp
                };
                
                // Create signature
                const signature = crypto
                    .createHmac('sha256', WEBHOOK_SECRET)
                    .update(JSON.stringify(webhookData))
                    .digest('hex');
                
                // Send webhook
                const response = await fetch(WEBHOOK_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Webhook-Signature': signature
                    },
                    body: JSON.stringify(webhookData)
                });
                
                if (response.ok) {
                    console.log(`Webhook sent successfully for ${result.portal}`);
                } else {
                    console.error(`Webhook failed for ${result.portal}:`, response.status);
                }
            }
        }
        
    } catch (error) {
        console.error('Error sending webhook:', error);
    }
}

// Helper functions for specific portal behaviors
async function handleSpecialCases(page, portalName) {
    switch (portalName) {
        case 'folha':
            await handleFolhaSpecialCases(page);
            break;
        case 'despesas':
            await handleDespesasSpecialCases(page);
            break;
        case 'contratos':
            await handleContratosSpecialCases(page);
            break;
    }
}

async function handleFolhaSpecialCases(page) {
    try {
        // Handle pagination if needed
        const paginationSelector = '.pagination-all, .show-all';
        const paginationButton = await page.$(paginationSelector);
        if (paginationButton) {
            await paginationButton.click();
            await page.waitForTimeout(2000);
        }
        
        // Handle employee filter
        const employeeFilter = await page.$('.employee-filter select');
        if (employeeFilter) {
            await employeeFilter.selectOption('all');
            await page.waitForTimeout(1000);
        }
        
    } catch (error) {
        console.warn('Folha special cases error:', error.message);
    }
}

async function handleDespesasSpecialCases(page) {
    try {
        // Handle expense category filter
        const categoryFilter = await page.$('.category-filter select');
        if (categoryFilter) {
            await categoryFilter.selectOption('all');
            await page.waitForTimeout(1000);
        }
        
        // Handle supplier filter
        const supplierFilter = await page.$('.supplier-filter select');
        if (supplierFilter) {
            await supplierFilter.selectOption('all');
            await page.waitForTimeout(1000);
        }
        
    } catch (error) {
        console.warn('Despesas special cases error:', error.message);
    }
}

async function handleContratosSpecialCases(page) {
    try {
        // Handle contract status filter
        const statusFilter = await page.$('.status-filter select');
        if (statusFilter) {
            await statusFilter.selectOption('all');
            await page.waitForTimeout(1000);
        }
        
        // Handle contract type filter
        const typeFilter = await page.$('.type-filter select');
        if (typeFilter) {
            await typeFilter.selectOption('all');
            await page.waitForTimeout(1000);
        }
        
    } catch (error) {
        console.warn('Contratos special cases error:', error.message);
    }
}

// Export for testing
module.exports = {
    scrapePortal,
    setDateFilters,
    checkExportSuccess,
    getCsvData
};