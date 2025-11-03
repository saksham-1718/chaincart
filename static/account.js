// account.js — clean version for Django server-side rendering

document.addEventListener('DOMContentLoaded', () => {

    // === Avatar upload auto-submit ===
    const fileInput = document.getElementById('avatar-file');
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const form = fileInput.closest('form');
            if (form) form.submit(); // Automatically submit form when avatar changes
        });
    }

    // === Sidebar navigation (Profile / Orders / Address / Payment / Security) ===
    const navItems = document.querySelectorAll('.account-nav li');
    const sections = document.querySelectorAll('.account-section');

    if (navItems.length && sections.length) {
        navItems.forEach(li => {
            li.addEventListener('click', () => {
                // highlight active nav item
                navItems.forEach(x => x.classList.remove('active'));
                li.classList.add('active');

                // show selected section, hide others
                const target = li.dataset.section;
                sections.forEach(sec => {
                    sec.classList.toggle('hidden', sec.id !== `${target}-section`);
                });
            });
        });
    }

    // === Optional UI enhancements ===
    // Expand/collapse forms, e.g., address or payment forms
    const toggleButtons = document.querySelectorAll('[data-toggle]');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = document.getElementById(btn.dataset.toggle);
            if (target) target.classList.toggle('hidden');
        });
    });

    console.log('Account page initialized (Django-rendered)');
});

const defaults = {
    profile: {
        fullName: '',
        email: '',
        phone: '',
        memberSince: '',
        avatar: ''
    },
    orders: [],
    addresses: [],
    payments: [],
    security: { twoFA: false }
};
