/* JS SideBar */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    sidebar.classList.toggle('open');
    content.classList.toggle('open');
}

