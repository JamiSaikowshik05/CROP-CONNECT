/* CropConnect translator.
 * Translates the text on each page into the language the visitor chose.
 * Dictionaries are loaded from static/i18n/<language>.js (built from locale/*.po by tools/i18n.py).
 * Any text without a translation stays in English.
 */
(() => {
    const I18N = window.CC_I18N || {lang: 'en', dict: {}};
    const dict = I18N.dict || {};
    const lang = (I18N.lang || 'en').toLowerCase();
    const hasDict = Object.keys(dict).length > 0;
    const attributeNames = ['placeholder', 'title', 'aria-label', 'alt'];
    const dynamicPrefixes = ['Recommended booking quantity:', '🌾 Predicted Yield:', 'Predicted Yield:', '🌾 Expected Yield:', 'Expected Yield:', 'Per acre:', 'Season:', 'Bring crop on', 'Expected Payment:', 'Confidence:', 'Pickup:', 'Requested:', 'Booked:', 'Offer from', 'Welcome,', 'Welcome back,', 'Grade:', 'Range:', 'Error:'];

    function lookup(key) {
        return Object.prototype.hasOwnProperty.call(dict, key) ? dict[key] : null;
    }

    // Telugu sentences whose numbers change from page to page (kept from the original script).
    function translateTelugu(leading, clean, trailing) {
        const moistureFailure = clean.match(/^Moisture ([\d.]+)% exceeds ([\d.]+)% limit$/i);
        if (moistureFailure) return `${leading}తేమ ${moistureFailure[1]}% (${moistureFailure[2]}% పరిమితి కంటే ఎక్కువ)${trailing}`;
        const foreignFailure = clean.match(/^Foreign matter ([\d.]+)% exceeds ([\d.]+)% limit$/i);
        if (foreignFailure) return `${leading}విదేశీ పదార్థాలు ${foreignFailure[1]}% (${foreignFailure[2]}% పరిమితి కంటే ఎక్కువ)${trailing}`;
        const qualityFailure = clean.match(/^(Damaged grains|Immature grains|Chalky grains) ([\d.]+)% exceeds ([\d.]+)% limit$/i);
        if (qualityFailure) {
            const labels = {'damaged grains': 'దెబ్బతిన్న గింజలు', 'immature grains': 'పక్వం కాని గింజలు', 'chalky grains': 'తెల్లమచ్చ గింజలు'};
            return `${leading}${labels[qualityFailure[1].toLowerCase()]} ${qualityFailure[2]}% (${qualityFailure[3]}% పరిమితి కంటే ఎక్కువ)${trailing}`;
        }
        const minimumFailure = clean.match(/^(Shelling outturn|Oil content) ([\d.]+)% below ([\d.]+)% minimum$/i);
        if (minimumFailure) {
            const label = minimumFailure[1].toLowerCase() === 'shelling outturn' ? 'పొట్టు తొలగింపు దిగుబడి' : 'నూనె శాతం';
            return `${leading}${label} ${minimumFailure[2]}% (${minimumFailure[3]}% కనిష్ఠం కంటే తక్కువ)${trailing}`;
        }
        if (/^Aflatoxin (contamination )?detected$/i.test(clean)) return `${leading}అఫ్లాటాక్సిన్ కలుషితం గుర్తించబడింది${trailing}`;

        const noPrivateOffers = clean.match(/^No private offers for (.+?) yet$/i);
        if (noPrivateOffers) return `${leading}${translateText(noPrivateOffers[1])}కు ప్రస్తుతం ప్రైవేట్ ఆఫర్లు లేవు${trailing}`;
        const allOffers = clean.match(/^All Offers for (.+)$/i);
        if (allOffers) return `${leading}${translateText(allOffers[1])}కు వచ్చిన ఆఫర్లన్నీ${trailing}`;
        const mspQuote = clean.match(/^Govt MSP:\s*(₹[\d,.]+)\s*\/qtl$/i);
        if (mspQuote) return `${leading}ప్రభుత్వ MSP: ${mspQuote[1]}/క్వింటాల్${trailing}`;
        const buyerPrice = clean.match(/^([+-]?₹[\d,.]+)\s+(above|below) MSP$/i);
        if (buyerPrice) return `${leading}${buyerPrice[1]} MSP ధర కంటే ${buyerPrice[2].toLowerCase() === 'above' ? 'ఎక్కువ' : 'తక్కువ'}${trailing}`;
        const paymentDays = clean.match(/^Payment in (\d+) days?$/i);
        if (paymentDays) return `${leading}${paymentDays[1]} రోజుల్లో చెల్లింపు${trailing}`;
        const advancePercent = clean.match(/^Advance: (\d+(?:\.\d+)?)%$/i);
        if (advancePercent) return `${leading}ముందస్తు చెల్లింపు: ${advancePercent[1]}%${trailing}`;
        const validDate = clean.match(/^Valid till: (.+)$/i);
        if (validDate) return `${leading}చెల్లుబాటు తేదీ: ${validDate[1]}${trailing}`;

        return null;
    }

    function translateText(text) {
        const leading = (text.match(/^\s*/) || [''])[0];
        const trailing = (text.match(/\s*$/) || [''])[0];
        const core = text.slice(leading.length, text.length - trailing.length || undefined);
        const clean = core.replace(/\s+/g, ' ');
        const direct = lookup(clean);
        if (direct !== null) return `${leading}${direct}${trailing}`;
        if (lang === 'te') {
            const special = translateTelugu(leading, clean, trailing);
            if (special !== null) return special;
        }
        for (const prefix of dynamicPrefixes) {
            if (clean.startsWith(prefix) && clean.length > prefix.length) {
                const translatedPrefix = lookup(prefix);
                if (translatedPrefix !== null) {
                    return `${leading}${translatedPrefix}${clean.slice(prefix.length)}${trailing}`;
                }
            }
        }
        return text;
    }

    window.CropConnectI18n = {
        translate(value) {
            return hasDict ? translateText(String(value)) : String(value);
        }
    };

    function translateTextNode(node) {
        if (!node || node.nodeType !== Node.TEXT_NODE) return;
        if (node.parentElement && node.parentElement.closest('script,style,code,[data-no-translate]')) return;
        const translated = translateText(node.nodeValue);
        if (translated !== node.nodeValue) node.nodeValue = translated;
    }

    function translateTree(root) {
        if (!root || root.nodeType === Node.ELEMENT_NODE && root.closest('script,style,code,[data-no-translate]')) return;

        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) translateTextNode(walker.currentNode);

        if (root.nodeType === Node.ELEMENT_NODE) {
            const elements = [root, ...root.querySelectorAll('*')];
            elements.forEach((element) => {
                attributeNames.forEach((name) => {
                    if (element.hasAttribute(name)) {
                        const value = element.getAttribute(name);
                        const translated = translateText(value);
                        if (translated !== value) element.setAttribute(name, translated);
                    }
                });
                if (['submit', 'button'].includes(element.type) && element.value) {
                    const translated = translateText(element.value);
                    if (translated !== element.value) element.value = translated;
                }
            });
        }
    }

    const OBSERVE = {childList: true, subtree: true, characterData: true};

    function start() {
        if (!hasDict) return;
        translateTree(document.documentElement);
        const observer = new MutationObserver((records) => {
            // Stop watching while this script makes its own edits. Without this, every
            // translated line was seen as a new change and translated again, which kept
            // the browser busy (the "page is having a problem" error).
            observer.disconnect();
            records.forEach((record) => {
                if (record.type === 'characterData') translateTextNode(record.target);
                record.addedNodes && record.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) translateTree(node);
                    else if (node.nodeType === Node.TEXT_NODE) translateTextNode(node);
                });
            });
            observer.observe(document.body, OBSERVE);
        });
        observer.observe(document.body, OBSERVE);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
    else start();
})();
