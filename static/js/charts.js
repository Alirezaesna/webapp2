// Chart.js configurations and functions

function createLoanStatusChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Approved', 'Completed', 'Pending', 'Rejected'],
      datasets: [{
        data: [
          data.approved || 0,
          data.completed || 0,
          data.pending || 0,
          data.rejected || 0
        ],
        backgroundColor: [
          '#28a745', // success
          '#17a2b8', // info
          '#ffc107', // warning
          '#dc3545'  // danger
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        }
      }
    }
  });
}

function createInstallmentStatusChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Paid', 'Unpaid', 'Overdue'],
      datasets: [{
        data: [
          data.paid || 0,
          data.unpaid || 0,
          data.overdue || 0
        ],
        backgroundColor: [
          '#28a745', // success
          '#17a2b8', // info
          '#dc3545'  // danger
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        }
      }
    }
  });
}

function createMonthlyTrendChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.months || [],
      datasets: [
        {
          label: 'Number of Loans',
          data: data.counts || [],
          backgroundColor: 'rgba(40, 167, 69, 0.6)',
          borderColor: '#28a745',
          borderWidth: 1,
          yAxisID: 'y',
        },
        {
          label: 'Loan Amount',
          data: data.amounts || [],
          type: 'line',
          fill: false,
          borderColor: '#17a2b8',
          backgroundColor: '#17a2b8',
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: 'Number of Loans'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: 'Loan Amount'
          },
          grid: {
            drawOnChartArea: false
          }
        }
      }
    }
  });
}

function createLoanProgressChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Paid', 'Remaining'],
      datasets: [{
        label: 'Amount',
        data: [
          data.paidAmount || 0,
          data.remainingAmount || 0
        ],
        backgroundColor: [
          '#28a745', // success
          '#ffc107'  // warning
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          stacked: true,
          ticks: {
            callback: function(value) {
              return value.toLocaleString();
            }
          }
        },
        y: {
          stacked: true
        }
      }
    }
  });
}

function createUserLoanChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Loan Amount',
        data: data.amounts || [],
        backgroundColor: data.colors || [],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value.toLocaleString();
            }
          }
        }
      }
    }
  });
}
