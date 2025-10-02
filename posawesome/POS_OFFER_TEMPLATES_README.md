# 🎯 POS Offer Templates - Comprehensive Test Scenarios

## 📋 Overview

This document outlines all test scenarios covered by the POS Offer template system. Each template represents a specific discount/gift scenario that can be duplicated and customized for production use.

## 🗂️ Template Categories

### 🕐 **Time-Based Templates (3 templates)**
Templates testing time-based restrictions with JSON time slots.

| Template | Description | Time Slots | Discount Type |
|----------|-------------|------------|---------------|
| `TEMPLATE_TIME_MORNING_DISCOUNT` | Morning discount 8:00-12:00 weekdays | Mon-Fri, 08:00-12:00 | 10% off items |
| `TEMPLATE_TIME_HAPPY_HOUR` | Happy hour discount 17:00-19:00 daily | All days, 17:00-19:00 | 15% off item groups |
| `TEMPLATE_TIME_OVERNIGHT` | Overnight discount 22:00-02:00 (weekends) | Fri-Sat, 22:00-02:00* | $25 off transaction |

*Overnight slots span midnight

### 📦 **Block-Based Discount Templates (3 templates)**
Templates testing block-based discounts with UOM validation.

| Template | Description | UOM | Block Size | Discount |
|----------|-------------|-----|------------|----------|
| `TEMPLATE_BLOCK_DISCOUNT_BEER` | Buy 6 beers (24 bottles/case), get discount | Thùng (Case) | 24 items | $50/block |
| `TEMPLATE_BLOCK_DISCOUNT_WATER` | Buy 12 bottles water, get discount per pack | Pack | 12 items | $30/block |
| `TEMPLATE_BLOCK_DISCOUNT_MIXED` | Mixed brand items block discount | Nos | 10 items | $20/block |

### 🎁 **Block-Based Gift Templates (2 templates)**
Templates testing block-based gifts with bonus gifts.

| Template | Description | UOM | Block Size | Gifts |
|----------|-------------|-----|------------|-------|
| `TEMPLATE_BLOCK_GIFT_BUY3_GET1` | Buy 3 drinks, get 1 free | Nos | 3 items | 1 gift/block |
| `TEMPLATE_BLOCK_GIFT_BONUS` | Buy 5 items, get 1 + bonus gift | Nos | 5 items | 1 + bonus gifts |

### 📊 **Tiered Pricing Templates (2 templates)**
Templates testing tiered pricing with JSON configuration.

| Template | Description | Tiers |
|----------|-------------|-------|
| `TEMPLATE_TIERED_VOLUME` | Volume discount tiers | 1-5: 0%, 6-10: 5%, 11+: 10% |
| `TEMPLATE_TIERED_FIXED_RATE` | Fixed rate tiers | 1-9: $100, 10-49: $90, 50+: $80 |

### 🔗 **Combined Scenario Templates (2 templates)**
Templates combining multiple features.

| Template | Description | Features Combined |
|----------|-------------|-------------------|
| `TEMPLATE_COMBO_TIME_BLOCK` | Morning bulk discount | Time + Block Discount |
| `TEMPLATE_COMBO_TIME_GIFT` | Weekend freebie | Time + Block Gift |

### ⚠️ **Edge Case Templates (3 templates)**
Templates testing edge cases and validation.

| Template | Description | Edge Case |
|----------|-------------|-----------|
| `TEMPLATE_EDGE_MIN_BLOCKS` | Minimum blocks requirement | Require 3 blocks minimum |
| `TEMPLATE_EDGE_MAX_BLOCKS` | Maximum blocks limit | Max 2 gifts |
| `TEMPLATE_EDGE_UOM_MISMATCH` | UOM validation test | Different UOM (should not apply) |

## 🚀 **How to Use Templates**

### 1. **Run Template Creation Script**
```bash
# In bench console
bench console < create_pos_offer_templates.py
```

### 2. **Review Created Templates**
- Go to POS Offer list
- Filter by `Is Template = 1`
- Review each template's configuration

### 3. **Duplicate for Production Use**
- Select a template
- Click "Duplicate" or create new offer
- Set `Is Template = 0`
- Customize parameters (item codes, amounts, etc.)
- Save as production offer

### 4. **Test Discount Calculations**
- Create test invoices with sample data
- Verify offers apply correctly
- Check logs for detailed processing info

## 📊 **Test Scenarios Matrix**

### Time-Based Testing
| Scenario | Expected Behavior |
|----------|------------------|
| Morning order (9:00 AM weekday) | Morning discount applies |
| Afternoon order (2:00 PM weekday) | No morning discount |
| Happy hour order (6:00 PM) | Happy hour discount applies |
| Overnight order (1:00 AM weekend) | Overnight discount applies |
| Invalid time slot | No time-based discount |

### Block-Based Discount Testing
| Scenario | Items | Expected Discount |
|----------|-------|------------------|
| 24 beers (1 case) | 24 x Beer | $50 discount |
| 48 beers (2 cases) | 48 x Beer | $100 discount |
| 60 beers (2.5 cases) | 60 x Beer | $100 discount (2 full cases) |
| 12 beers (0.5 case) | 12 x Beer | No discount (below minimum) |
| Mixed UOM items | Various UOMs | Only matching UOM items discounted |

### Block-Based Gift Testing
| Scenario | Items | Expected Gifts |
|----------|-------|----------------|
| 6 drinks | 6 x Drink | 2 free drinks |
| 15 drinks | 15 x Drink | 5 free drinks |
| 16 drinks | 16 x Drink | 5 free drinks (max 5 gifts) |
| 2 drinks | 2 x Drink | No gifts (below minimum) |

### Tiered Pricing Testing
| Scenario | Quantity | Expected Rate |
|----------|----------|---------------|
| 3 items | 3 | Original rate |
| 8 items | 8 | 5% discount |
| 15 items | 15 | 10% discount |
| 100 items | 100 | 10% discount |

### Combined Scenarios Testing
| Scenario | Conditions | Expected Result |
|----------|------------|-----------------|
| Morning + 20 boxes | Weekday 9:00 AM + 20 boxes | Block discount applies |
| Weekend + 50 items | Saturday 2:00 PM + 50 items | Gift offer applies |
| Invalid time + valid blocks | Outside time slots + valid blocks | No discount/gift |

## 🔧 **Sample Test Data**

The script creates sample items for testing:

- **BEER_500ML**: Beer item for block testing
- **WATER_1L**: Water item for pack testing
- **COKE_330ML**: Coke item for brand testing
- **SAMPLE_ITEM**: Generic gift item
- **BONUS_ITEM**: Bonus gift item

## 📈 **Validation Checklist**

### ✅ **Template Creation**
- [ ] All 15 templates created successfully
- [ ] Sample items created
- [ ] No duplicate templates

### ✅ **Time-Based Validation**
- [ ] Morning discount applies correctly
- [ ] Happy hour discount applies correctly
- [ ] Overnight slots work across midnight
- [ ] Invalid time slots are rejected

### ✅ **Block-Based Validation**
- [ ] UOM validation works correctly
- [ ] Block calculations are accurate
- [ ] Min/max block limits enforced
- [ ] Proportional discount distribution

### ✅ **Gift Validation**
- [ ] Gift items added correctly
- [ ] Bonus gifts work with JSON config
- [ ] Gift limits enforced
- [ ] No duplicate gifts

### ✅ **Tiered Pricing Validation**
- [ ] JSON parsing works correctly
- [ ] Tier boundaries respected
- [ ] Different pricing types (fixed, percentage) work

### ✅ **Integration Testing**
- [ ] Multiple offers don't conflict
- [ ] Template offers excluded from calculations
- [ ] Production offers work correctly
- [ ] Error handling robust

## 🐛 **Common Issues & Solutions**

### Issue: Template not applying
**Solution**: Check time slots, UOM matching, quantity conditions

### Issue: Wrong discount amount
**Solution**: Verify block calculations, tier configurations

### Issue: Gift not added
**Solution**: Check gift item exists, UOM validation, block limits

### Issue: JSON parsing errors
**Solution**: Validate JSON syntax in time slots/tiered pricing

## 📞 **Support**

For issues with templates:
1. Check frappe logs for detailed error messages
2. Verify template configuration matches test scenario
3. Test with sample data first
4. Review validation checklist above

## 🎯 **Next Steps**

After template validation:
1. ✅ Phase 1: Database Migration (Complete)
2. ✅ Phase 2: Backend Implementation (Complete)
3. 🔄 Phase 3: Validation & Testing (In Progress)
4. 🔄 Phase 4: Frontend Integration (Pending)

**Total Progress: 80% Complete** 🚀