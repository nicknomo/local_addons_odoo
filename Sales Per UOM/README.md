# Sell with Pricing by varied UoM / Flooring Sales
   The purpose of this module is to allow you to price out a sale in a unit of measure other than your default unit of sale.  For instance, lets say you sell tile by the carton, but price it out by the square foot (SF).  With this module, you can price your sale by the SF, but sell by the carton.

# Contact

   electronic mail: nick (at) theserverexpert (dot) com
   website: https://github.com/nicknomo/local_addons_odoo

# Installation

   Please ensure you've configured a location for Odoo to locally load apps.  Copy this folder into there. Go to your odoo web interface, and go into the Apps tab. Click on "Update module list". Then search for "Sell with Pricing by varied UoM / Flooring Sales" within your App list, and then install.

# Prerequisites

   You must be using Odoo v10 or possibly higher.  This module is only confirmed with v10. It will most likely not work with earlier versions, due to changes in the Odoo menu system.  

# Usage

   This module relies on the "Per Prdouct UoM" module. The information on the usage is added after this section. The full README.md can be found in the folder of that module. Please ensure that is properly set up and configured first to take full advantage of this module.
   
   This module changes the Sales/Quotation screen.  A new menu interface has been added above where the order lines are entered.  You can use this menu by selecting a product and a unit of measure.  This will show you the list price and the cost using that unit of measure.  For example: let's say you created a product (e.g. "Tile") with a default unit of Box for sale and supply.  Your Price is $100 and Cost is $10.  Now lets say you create a unit of measure call "piece", which is 1/10 of a Box.  Now, you go to this modules interface in the Sale/Quote screen, and you put your item and choose "piece" as your unit of measure.  This module will show your Price as being $10 / PC and cost being $1 / PC .
   
   In order to size your order, select the quantity under the "Pricing Quantity" entry.  Going back to our example, lets say you needed 95 pieces.  Since we only sell by the box, our module will list an estimated quantity. In this case, the interface suggest 9.5 Boxes.  The Sales person is left with the final decision for actual quantity.
   
   After the sales person enters the quantity, they are left to decide the price. The price defaults to the list price, however this can be changed before the line is added.  The unit of measure of the price is displayed first, and the value is entered immediately after.  The following line lists the unit of sale, and the saleman is left to enter the quantity.  
   
   Once you hit the Add Line button, the line is added to the order.  Keep in mind that once a line is placed on the order, the Odoo default behavior resumes.  Changing the UoM after the line is added will NOT make the appropriate changes in either quantity or price. If you wish to make these adjustments, it is recommended you remove the line and use the user interface added by this module.
   
   

    ###Per Product UoM usage:
   
    The intention of this module is to help you reuse similarly named units of measure in an organized way.  Using this module, you can create a units of measure assign it to a UoM class. You can then assign this class to a product. This is useful if 1 box of Product A is 4 LB, but 1 box of product B is 20 LB.  As long as product A and Product B are assigned a different UoM class, they may use the same unit of measure names, but the correct box to LB conversions can be maintained.
   
    Your first step is to enable different units of measure in Odoo.  Go into Inventory->settings.  Go to the "Products" section of the page, and choose the option "Some products may be sold/purchased in different units of measure (advanced)"

    After this is done, you must first enter the "Per Product Mod" tab.  Click on the menu seletion for "Product UOM Class".  You must then create a Product UOM Class. At this point, only a name is required. This class will later be assigned to a Product.  The product will then be restricted to UoM's within that class/category.  Units of measure must be unique to that UoM class. 

    After the class is created, you must select the menu entry for "Local UOM Entries".  Here, you create a unit of measure and assign it to a UOM class. You can create multiple units of measure and assign them to a class.  

    After the UoM class, and units of measure are assigned to it, you can edit a product and assign this UoM class to the product.  The sale and purchasing UoM can then be selected from this UoM class.  If multiple products use the same units of measure, this class can be assigned to other those other products as well.

# Known Issues
   
   This module relies on the Per Product UoM module (which is probably included or in a repository with this module).  The Per Product UoM module does not uninstall all related data from Odoo when the module is removed.  Please see that modules documentation for a further explanation of the issue.There is a README.md in the folder for that module.
     