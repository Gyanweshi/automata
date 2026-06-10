/**
 * PDF Image Extractor Utility
 * 
 * Provides high-quality image extraction from PDFs for Node.js agents.
 * Utilizes `poppler-utils` (specifically `pdftocairo` and `pdfimages`) 
 * to ensure maximum fidelity and clarity.
 */
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const path = require('node:path');
const fs = require('node:fs/promises');

const execFileAsync = promisify(execFile);

/**
 * Extracts embedded images from a PDF in their original, uncompressed quality.
 * Best for retrieving photos or assets exactly as they were placed in the PDF.
 * 
 * @param {string} pdfPath - Absolute or relative path to the PDF file.
 * @param {string} outputDir - Directory to save extracted images.
 * @param {string} prefix - Prefix for the generated image files.
 * @returns {Promise<string>} - The output directory containing the images.
 */
async function extractOriginalImages(pdfPath, outputDir, prefix = 'image') {
    await fs.mkdir(outputDir, { recursive: true });
    
    // -all extracts in original format (png, jpeg, tiff, etc.)
    const outputPath = path.join(outputDir, prefix);
    await execFileAsync('pdfimages', ['-all', pdfPath, outputPath]);
    
    return outputDir;
}

/**
 * Renders full PDF pages as high-quality PNGs.
 * Best for slides, vector graphics, or text heavy pages where you need a crisp rendering.
 * 
 * @param {string} pdfPath - Absolute or relative path to the PDF file.
 * @param {string} outputDir - Directory to save rendered images.
 * @param {string} prefix - Prefix for the generated image files.
 * @param {number} dpi - Resolution of the output image (default 300 for high quality).
 * @returns {Promise<string>} - The output directory containing the images.
 */
async function renderHighQualityPages(pdfPath, outputDir, prefix = 'page', dpi = 300) {
    await fs.mkdir(outputDir, { recursive: true });
    
    const outputPath = path.join(outputDir, prefix);
    
    // pdftocairo with -png and -r (resolution in DPI) provides excellent crisp renders.
    // -transp can be added if transparent background is desired.
    await execFileAsync('pdftocairo', ['-png', '-r', dpi.toString(), pdfPath, outputPath]);
    
    return outputDir;
}

// Example CLI usage:
// Run with: node scripts/extract-pdf-images.js <path-to-pdf>
if (require.main === module) {
    const pdf = process.argv[2];
    if (!pdf) {
        console.error("Usage: node extract-pdf-images.js <path-to-pdf>");
        process.exit(1);
    }
    
    const outDir = path.join(process.cwd(), 'workspace', 'pdf-extracts', path.basename(pdf, '.pdf'));
    
    console.log(`Extracting high-quality renders from ${pdf} at 300 DPI...`);
    renderHighQualityPages(pdf, path.join(outDir, 'renders'))
        .then(() => console.log(`Renders saved to ${path.join(outDir, 'renders')}`))
        .catch(console.error);
        
    console.log(`Extracting original embedded assets...`);
    extractOriginalImages(pdf, path.join(outDir, 'assets'))
        .then(() => console.log(`Assets saved to ${path.join(outDir, 'assets')}`))
        .catch(console.error);
}

module.exports = {
    extractOriginalImages,
    renderHighQualityPages,
};
