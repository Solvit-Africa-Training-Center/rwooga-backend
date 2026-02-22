# Paypack Sandbox Credentials Request

## Email Template

**To:** support@paypack.rw  
**Subject:** Request for Sandbox/Test API Credentials

---

Hi Paypack Team,

I'm developing an e-commerce platform called **Rwooga** and need sandbox credentials for testing the Mobile Money integration before going live.

**Current Production Details:**
- Client ID: `9eb100fa-0a7b-11f1-bfd1-deadd43720af`
- Integration Status: Successfully integrated, ready for testing

**Request:**
Please provide the following for sandbox/test environment:
1. Sandbox Client ID
2. Sandbox Client Secret
3. Test phone numbers for different scenarios:
   - Successful payment
   - Failed payment
   - Pending/timeout scenarios
4. Any specific testing guidelines or limitations

**Use Case:**
I need to thoroughly test the payment flow including:
- Payment initiation (cashin)
- Status checking
- Error handling
- Frontend integration

**Timeline:**
I'm ready to start testing as soon as I receive the credentials.

Thank you for your support!

Best regards,  
[Your Name]  
Rwooga E-commerce Platform  
Email: mutheogene61@gmail.com

---

## What to Expect

**Response Time:** 24-48 hours (typically)

**What You'll Receive:**
- Sandbox Client ID (different from production)
- Sandbox Client Secret (different from production)
- Test phone numbers (usually format: 078XXXXXXX)
- Testing documentation/guidelines

**Next Steps After Receiving:**
1. Update `.env` file with sandbox credentials
2. Ensure `PAYPACK_MODE=sandbox` is set
3. Restart Django server
4. Start testing!

---

## Current Configuration Status

✅ **Ready for Sandbox:**
- Environment variables configured
- Code updated to support sandbox mode
- Testing guide created

⏳ **Waiting for:**
- Sandbox credentials from Paypack

---

## Alternative: Test NOW with Card Simulation

While waiting for Paypack sandbox, you can test card payments immediately:

```bash
# Your server is already configured!
python manage.py runserver
```

**Test Card Payment:**
```json
POST http://localhost:8000/api/payments/initiate/

{
  "amount": 5000,
  "paymentMethod": "card",
  "cardNumber": "4242424242424242",
  "expiryDate": "12/25",
  "cvv": "123",
  "customerName": "Test User",
  "customerEmail": "test@example.com"
}
```

**Expected Result:**
- ✅ Success after 5 seconds (any amount except 12345)
- ❌ Failure after 5 seconds (amount = 12345)

---

## Troubleshooting

**If you don't hear back within 48 hours:**
- Send a follow-up email
- Try their website contact form
- Check if they have a support phone number

**If sandbox is not available:**
- Ask about their testing recommendations
- Request test merchant account
- Consider Flutterwave test mode as alternative
