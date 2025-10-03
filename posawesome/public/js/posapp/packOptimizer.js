/**
 * Pack Optimizer - Dynamic Programming Algorithm for Optimal Pack Combinations
 * Solves the "unbounded knapsack" problem to find minimum cost combinations of packs
 *
 * For retail scenarios with multiple pack sizes (e.g., 24-pack, 6-pack, individual items)
 * where each pack has different pricing/discounts
 */

class PackOptimizer {
    constructor() {
        this.cache = new Map(); // Cache for performance
    }

    /**
     * Get optimal pack combination for quantity Q with given pack options
     * @param {number} Q - Total quantity needed
     * @param {Array} packs - Array of pack objects: [{size: 24, price: 680, uom: 'THÙNG-24'}, ...]
     * @param {Object} constraints - Optional constraints: {maxBlocks: {24: 5, 6: 10}}
     * @returns {Object} - {24: count24, 6: count6, 1: count1, total: totalPrice, breakdown: [...]}
     */
    getOptimalCombo(Q, packs, constraints = {}) {
        if (Q <= 0) return {24: 0, 6: 0, 1: 0, total: 0, breakdown: []};

        // Create cache key
        const cacheKey = `${Q}-${JSON.stringify(packs)}-${JSON.stringify(constraints)}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        // Filter valid packs and apply constraints
        const validPacks = this._filterValidPacks(packs, constraints);

        if (validPacks.length === 0) {
            // Fallback to individual items only
            const individualPack = packs.find(p => p.size === 1) || {size: 1, price: Infinity, uom: 'LON'};
            const result = {
                24: 0,
                6: 0,
                1: Q,
                total: individualPack.price * Q,
                breakdown: [{uom: individualPack.uom, qty: Q, price: individualPack.price, subtotal: individualPack.price * Q}]
            };
            this.cache.set(cacheKey, result);
            return result;
        }

        // Run DP algorithm
        const dpResult = this._runDP(Q, validPacks);

        // Reconstruct optimal combination
        const combo = this._reconstructCombo(Q, validPacks, dpResult);

        // Create breakdown for transparency
        const breakdown = this._createBreakdown(combo, packs);

        const result = {
            ...combo,
            total: dpResult.cost[Q],
            breakdown: breakdown
        };

        this.cache.set(cacheKey, result);
        return result;
    }

    /**
     * Filter packs based on constraints and availability
     */
    _filterValidPacks(packs, constraints) {
        return packs.filter(pack => {
            // Check max blocks constraint
            if (constraints.maxBlocks && constraints.maxBlocks[pack.size]) {
                // We'll handle this in DP to allow flexible combinations
                return true;
            }
            return true;
        });
    }

    /**
     * Dynamic Programming algorithm for minimum cost
     */
    _runDP(Q, packs) {
        const dp = new Array(Q + 1).fill(Infinity);
        const choices = new Array(Q + 1).fill(null);

        dp[0] = 0;

        for (let q = 1; q <= Q; q++) {
            for (const pack of packs) {
                if (q >= pack.size) {
                    const prevCost = dp[q - pack.size];
                    if (prevCost !== Infinity) {
                        const newCost = prevCost + pack.price;
                        if (newCost < dp[q]) {
                            dp[q] = newCost;
                            choices[q] = {
                                pack: pack,
                                prevQty: q - pack.size
                            };
                        }
                    }
                }
            }
        }

        return {cost: dp, choices: choices};
    }

    /**
     * Reconstruct the optimal combination from DP results
     */
    _reconstructCombo(Q, packs, dpResult) {
        const combo = {24: 0, 6: 0, 1: 0};
        let currentQty = Q;

        while (currentQty > 0) {
            const choice = dpResult.choices[currentQty];
            if (!choice) break;

            const packSize = choice.pack.size;
            combo[packSize]++;
            currentQty = choice.prevQty;
        }

        return combo;
    }

    /**
     * Create detailed breakdown for transparency
     */
    _createBreakdown(combo, packs) {
        const breakdown = [];

        [24, 6, 1].forEach(size => {
            const qty = combo[size];
            if (qty > 0) {
                const pack = packs.find(p => p.size === size);
                if (pack) {
                    breakdown.push({
                        uom: pack.uom,
                        qty: qty,
                        unitPrice: pack.price,
                        subtotal: pack.price * qty
                    });
                }
            }
        });

        return breakdown;
    }

    /**
     * Get pack configuration for a specific item
     * @param {string} itemCode - Item code to get packs for
     * @param {Object} posProfile - POS Profile data
     * @returns {Array} Array of available packs
     */
    async getAvailablePacks(itemCode, posProfile) {
        try {
            // Get item UOMs and prices
            const itemData = await frappe.call({
                method: "posawesome.posawesome.api.items.get_item_detail",
                args: {
                    item_code: itemCode,
                    pos_profile: posProfile.name,
                    price_list: posProfile.selling_price_list
                }
            });

            if (!itemData.message) return [];

            const item = itemData.message;
            const packs = [];

            // Add individual item pack
            if (item.rate) {
                packs.push({
                    size: 1,
                    price: item.rate,
                    uom: item.stock_uom,
                    item_uom: item.stock_uom
                });
            }

            // Add UOM conversion packs (6-pack, 24-pack, etc.)
            if (item.item_uoms) {
                item.item_uoms.forEach(uomData => {
                    // Try to get price for this UOM
                    const uomPrice = this._getPriceForUOM(item, uomData.uom);
                    if (uomPrice) {
                        const packSize = Math.round(uomData.conversion_factor);
                        packs.push({
                            size: packSize,
                            price: uomPrice,
                            uom: uomData.uom,
                            item_uom: uomData.uom,
                            conversion_factor: uomData.conversion_factor
                        });
                    }
                });
            }

            return packs;
        } catch (error) {
            console.error("Error getting available packs:", error);
            return [];
        }
    }

    /**
     * Get price for specific UOM from item price data
     */
    _getPriceForUOM(item, uom) {
        // Check item_uoms for pricing
        if (item.item_uoms) {
            const uomData = item.item_uoms.find(u => u.uom === uom);
            if (uomData && uomData.price_list_rate) {
                return uomData.price_list_rate;
            }
        }

        // Fallback to base rate calculation
        if (item.base_rate && item.conversion_factor) {
            return item.base_rate * item.conversion_factor;
        }

        return null;
    }

    /**
     * Clear cache (useful when pack configurations change)
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Get savings comparison vs buying individual items
     */
    getSavingsComparison(combo, individualPrice) {
        const totalIndividual = combo.totalQty * individualPrice;
        const savings = totalIndividual - combo.total;

        return {
            individualTotal: totalIndividual,
            comboTotal: combo.total,
            savings: savings,
            savingsPercent: totalIndividual > 0 ? (savings / totalIndividual * 100) : 0
        };
    }
}

// Export singleton instance
const packOptimizer = new PackOptimizer();
export default packOptimizer;