let currentBillItems = [];
        let billCounter = 3;

function showModule(moduleId, event) {
    // Hide all modules
    const modules = document.querySelectorAll('.module');
    modules.forEach(module => module.classList.remove('active'));

    // Remove 'active' from all tabs
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Show the selected module
    const targetModule = document.getElementById(moduleId);
    if (targetModule) {
        targetModule.classList.add('active');
    }

    // Add active class to clicked tab
    if (event && event.target) {
        event.target.classList.add('active');
    }
}



        // Admin Module Functions
        function addUser() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('userEmail').value;
            const role = document.getElementById('userRole').value;

            if (!username || !email) {
                alert('Please fill in all fields');
                return;
            }

            const table = document.getElementById('usersTable').getElementsByTagName('tbody')[0];
            const newRow = table.insertRow();
            newRow.innerHTML = `
                <td>${username}</td>
                <td>${email}</td>
                <td>${role}</td>
                <td>Active</td>
                <td><button class="btn btn-danger" onclick="deleteUser(this)">Delete</button></td>
            `;

            // Clear form
            document.getElementById('username').value = '';
            document.getElementById('userEmail').value = '';
            alert('User added successfully!');
        }

        function deleteUser(button) {
            if (confirm('Are you sure you want to delete this user?')) {
                button.closest('tr').remove();
                alert('User deleted successfully!');
            }
        }

        function addZone() {
            const zoneName = document.getElementById('zoneName').value;
            const zoneType = document.getElementById('zoneType').value;
            const capacity = document.getElementById('zoneCapacity').value;

            if (!zoneName || !capacity) {
                alert('Please fill in all fields');
                return;
            }

            // Add to storage location dropdown
            const select = document.getElementById('storageLocation');
            const option = document.createElement('option');
            option.value = zoneName.toLowerCase().replace(/\s+/g, '-');
            option.textContent = `${zoneName} (${zoneType})`;
            select.appendChild(option);

            // Clear form
            document.getElementById('zoneName').value = '';
            document.getElementById('zoneCapacity').value = '';
            alert('Storage zone added successfully!');

            // Update total zones count
            const totalZones = document.getElementById('totalZones');
            totalZones.textContent = parseInt(totalZones.textContent) + 1;
        }

        // Storage Module Functions
function addMedicine() {
    const data = {
        medicine_name: document.getElementById("medicineName").value,
        generic_name: document.getElementById("genericName").value,
        batch_no: document.getElementById("batchNumber").value,
        quantity: parseInt(document.getElementById("quantity").value),
        mfg_date: document.getElementById("mfgDate").value,
        expiry_date: document.getElementById("expiryDate").value,
        storage_location: document.getElementById("storageLocation").value,
        unit_price: parseFloat(document.getElementById("unitPrice").value)
    };

    fetch('/add_medicine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => response.json())
      .then(result => {
          if (result.status === 'success') {
              alert("Medicine added successfully!");
              location.reload();  // Reload page to show new data
          } else {
              alert("Failed to add medicine.");
          }
      });
}


        function editMedicine(button) {
            const row = button.closest('tr');
            const cells = row.cells;
            
            // Fill form with current values
            document.getElementById('medicineName').value = cells[0].textContent;
            document.getElementById('genericName').value = cells[1].textContent;
            document.getElementById('batchNumber').value = cells[2].textContent;
            document.getElementById('quantity').value = cells[3].textContent;
            document.getElementById('expiryDate').value = cells[4].textContent;
            document.getElementById('unitPrice').value = cells[6].textContent.replace('₹', '');

            // Remove the row for editing
            row.remove();
            alert('Medicine loaded for editing. Update the details and click Add Medicine.');
        }

        function deleteMedicine(button) {
            if (confirm('Are you sure you want to delete this medicine?')) {
                button.closest('tr').remove();
                alert('Medicine deleted successfully!');
            }
        }

        function searchMedicines(searchTerm) {
            const table = document.getElementById('inventoryTable');
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const medicineName = row.cells[0].textContent.toLowerCase();
                const genericName = row.cells[1].textContent.toLowerCase();
                
                if (medicineName.includes(searchTerm.toLowerCase()) || 
                    genericName.includes(searchTerm.toLowerCase())) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        }

        function generateInventoryReport() {
            alert('Inventory report generated successfully! Check your downloads folder.');
        }


        // Billing Module Functions
        function addToBill() {
    const medicine = document.getElementById('billMedicine');
    const quantity = parseInt(document.getElementById('billQuantity').value);

    if (!medicine.value || !quantity) {
        alert('Please select a medicine and enter quantity');
        return;
    }

    const medicineText = medicine.options[medicine.selectedIndex].text;
    const medicineName = medicineText.split(' - ')[0];
    const price = parseFloat(medicine.options[medicine.selectedIndex].getAttribute('data-price'));
    const total = price * quantity;

    currentBillItems.push({
        id: medicine.value, // store medicine ID
        name: medicineName,
        quantity: quantity,
        price: price,
        total: total
    });

    updateBillDisplay(); // show bill items

    medicine.value = '';
    document.getElementById('billQuantity').value = '';
}


        function updateBillDisplay() {
            const billItemsDiv = document.getElementById('billItems');
            
            if (currentBillItems.length === 0) {
                billItemsDiv.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No items added yet</p>';
                document.getElementById('billTotal').textContent = 'Total: ₹0.00';
                return;
            }

            let html = '';
            currentBillItems.forEach((item, index) => {
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #e0e0e0;">
                        <div>
                            <strong>${item.name}</strong><br>
                            <small>Qty: ${item.quantity} × ₹${item.price.toFixed(2)}</small>
                        </div>
                        <div style="text-align: right;">
                            <strong>₹${item.total.toFixed(2)}</strong><br>
                            <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.8em;" onclick="removeFromBill(${index})">Remove</button>
                        </div>
                    </div>
                `;
            });
            
            billItemsDiv.innerHTML = html;
            calculateTotal();
        }

        function removeFromBill(index) {
            currentBillItems.splice(index, 1);
            updateBillDisplay();
        }

        function calculateTotal() {
            let subtotal = currentBillItems.reduce((sum, item) => sum + item.total, 0);
            
            const discount = parseFloat(document.getElementById('discount').value) || 0;
            const tax = parseFloat(document.getElementById('tax').value) || 0;
            
            const discountAmount = (subtotal * discount) / 100;
            const afterDiscount = subtotal - discountAmount;
            const taxAmount = (afterDiscount * tax) / 100;
            const finalTotal = afterDiscount + taxAmount;
            
            document.getElementById('billTotal').textContent = `Total: ₹${finalTotal.toFixed(2)}`;
        }

function generateBill() {
    const customerName = document.getElementById('customerName').value;
    const customerPhone = document.getElementById('customerPhone').value;
    const discount = parseFloat(document.getElementById('discount').value || 0);
    const tax = parseFloat(document.getElementById('tax').value || 0);

    if (!customerName || currentBillItems.length === 0) {
        alert('Please enter customer name and add at least one item.');
        return;
    }

    fetch('/generate_bill', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            customer_name: customerName,
            customer_phone: customerPhone,
            discount: discount,
            tax: tax,
            items: currentBillItems
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert('✅ Bill generated successfully!');
            clearBill(); // clear UI
        } else {
            alert('❌ Failed to generate bill.');
        }
    });
}


        function clearBill() {
            currentBillItems = [];
            document.getElementById('customerName').value = '';
            document.getElementById('customerPhone').value = '';
            document.getElementById('discount').value = '';
            document.getElementById('tax').value = '18';
            updateBillDisplay();
        }

        function viewBill(button) {
            const row = button.closest('tr');
            const billId = row.cells[0].textContent;
            alert(`Viewing bill ${billId} - Full bill details would be displayed in a modal or new window.`);
        }

        function printBill(button) {
            const row = button.closest('tr');
            const billId = row.cells[0].textContent;
            alert(`Printing bill ${billId}...`);
        }

        // Sales Module Functions
        function filterSales() {
    const fromDate = document.getElementById("salesDateFrom").value;
    const toDate = document.getElementById("salesDateTo").value;
    const category = document.getElementById("salesCategory").value;

    const url = `/filter_sales?from=${fromDate}&to=${toDate}&category=${encodeURIComponent(category)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector("#salesTable tbody");
            tbody.innerHTML = ""; // Clear old rows

            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6">No data found</td></tr>`;
                return;
            }

            data.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${row.date}</td>
                    <td>${row.medicine_name}</td>
                    <td>${row.quantity}</td>
                    <td>₹${parseFloat(row.unit_price).toFixed(2)}</td>
                    <td>₹${parseFloat(row.total_amount).toFixed(2)}</td>
                    <td>${row.customer}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error("Error fetching sales data:", error);
        });
}
